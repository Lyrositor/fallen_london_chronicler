// ==UserScript==
// @name        Fallen London Chronicler
// @namespace   Violentmonkey Scripts
// @match       https://www.fallenlondon.com/
// @grant       GM.xmlHttpRequest
// @version     1.1.0
// @author      Lyrositor
// @description A tool for recording and exporting Fallen London content.
// @downloadURL {{download_url}}
// ==/UserScript==

const API_KEY = "{{api_key}}";
const LISTENER_URL = "{{submit_url}}";
const SUBMIT_AREA_URL = LISTENER_URL + "/area";
const SUBMIT_POSSESSIONS_URL = LISTENER_URL + "/possessions";
const SUBMIT_SETTING_URL = LISTENER_URL + "/setting";
const SUBMIT_OPPORTUNITIES_URL = LISTENER_URL + "/opportunities";
const SUBMIT_STORYLET_LIST_URL = LISTENER_URL + "/storylet/list";
const SUBMIT_STORYLET_VIEW_URL = LISTENER_URL + "/storylet/view";
const SUBMIT_STORYLET_OUTCOME_URL = LISTENER_URL + "/storylet/outcome";

const PHASE_STORYLET_LIST = "Available";
const PHASE_STORYLET_VIEW = "In";
const PHASE_STORYLET_VIEW_ITEM = "InItemUse"
const PHASE_STORYLET_OUTCOME = "End";

const CHOOSE_BRANCH_URL = "https://api.fallenlondon.com/api/storylet/choosebranch";

let areaId = null;
let settingId = null;
let isLinkingFromBranch = null;
let lastOutcomeObservationId = null;

function submit(url, data, description) {
    console.log(`Submitting ${description}`);
    data.apiKey = API_KEY;
    GM.xmlHttpRequest({
        method: "POST",
        url: url,
        data: JSON.stringify(data),
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        synchronous: true,
        onload: function (response) {
            let data = {};
            try {
                data = JSON.parse(response.responseText);
            } catch (error) {
                console.error(`Failed to submit ${description}: ` + response.responseText);
                return;
            }
            if (data.success) {
                console.log(`Successfully submitted ${description}`);
                if (data.outcomeObservationId != null) {
                    lastOutcomeObservationId = data.outcomeObservationId;
                }
                if (data.newAreaId != null) {
                    areaId = data.newAreaId;
                }
                if (data.newSettingId != null) {
                    settingId = data.newSettingId;
                }
            } else {
                console.error(`Failed to submit ${description}: ` + data.error)
            }
        },
        onerror: function (response) {
            console.error(`Failed to submit ${description}: ` + response);
        }
    });
}

function submitPossessions(possessions) {
    submit(SUBMIT_POSSESSIONS_URL, {possessions}, `possessions list`);
}

function submitAreaData(area) {
    areaId = area.id;
    submit(SUBMIT_AREA_URL, {area, settingId}, `area ${areaId}`);
}

function submitSettingData(setting) {
    settingId = setting.id;
    submit(SUBMIT_SETTING_URL, {setting, areaId}, `setting ${settingId}`);
}

function submitBranchOutcomeData(branchId, chooseBranchRequestData) {
    if (areaId == null) {
        console.warn("Area ID is not known so storylet outcome might be incomplete");
    }
    if (settingId == null) {
        console.warn("Storylet ID is not known so storylet outcome might be incomplete");
    }
    const branchOutcomeData = {
        isLinkingFromOutcomeObservation: null,
        branchId,
        areaId,
        settingId,
    };
    if (lastOutcomeObservationId != null) {
        branchOutcomeData.isLinkingFromOutcomeObservation = lastOutcomeObservationId;
        lastOutcomeObservationId = null;
    }
    if (chooseBranchRequestData.phase === PHASE_STORYLET_OUTCOME) {
        branchOutcomeData.endStorylet = chooseBranchRequestData.endStorylet;
        branchOutcomeData.messages = chooseBranchRequestData.messages;
        isLinkingFromBranch = chooseBranchRequestData.endStorylet.isLinkingEvent;
    }
    if (chooseBranchRequestData.storylet) {
        branchOutcomeData.redirect = chooseBranchRequestData.storylet;
    }
    submit(SUBMIT_STORYLET_OUTCOME_URL, branchOutcomeData, `storylet outcome of branch ${branchId}`);
}

function submitOpportunitiesData(displayCards) {
    if (areaId == null) {
        console.warn("Not submitting opportunity as area ID is not yet known");
        return;
    }
    if (settingId == null) {
        console.warn("Not submitting opportunity as setting ID is not yet known");
        return;
    }
    submit(
        SUBMIT_OPPORTUNITIES_URL,
        {areaId, settingId, displayCards},
        `opportunities in area ${areaId}/setting ${settingId}`
    );
}

function submitStoryletListData(storylets) {
    if (areaId == null) {
        console.warn("Not submitting storylet list as area ID is not yet known");
        return;
    }
    if (settingId == null) {
        console.warn("Not submitting storylet list as setting ID is not yet known");
        return;
    }
    if (lastOutcomeObservationId != null) {
        lastOutcomeObservationId = null;
    }
    submit(
        SUBMIT_STORYLET_LIST_URL,
        {areaId, settingId, storylets},
        `storylet list in area ${areaId}/setting ${settingId}`
    );
}

function submitStoryletData(storylet, inInventory = false) {
    if (areaId == null) {
        console.warn("Not submitting storylet as area ID is not yet known");
        return;
    }
    if (settingId == null) {
        console.warn("Not submitting storylet as setting ID is not yet known");
        return;
    }
    const storyletData = {
        isLinkingFromOutcomeObservation: null,
        areaId,
        settingId,
        storylet,
        inInventory,
    };
    if (isLinkingFromBranch) {
        storyletData.isLinkingFromOutcomeObservation = lastOutcomeObservationId;
        lastOutcomeObservationId = null;
        isLinkingFromBranch = false;
    }
    submit(SUBMIT_STORYLET_VIEW_URL, storyletData, `storylet ${storylet.id}`);
}

function getBranchId(xmlHttpRequest) {
    if (xmlHttpRequest.requestArguments && xmlHttpRequest.requestArguments[0]) {
        try {
            const requestData = JSON.parse(xmlHttpRequest.requestArguments[0]);
            if ("branchId" in requestData) {
                return requestData["branchId"];
            }
        } catch (error) {}
    }
    return null;
}

(function (send) {
    XMLHttpRequest.prototype.send = function () {
        this.requestArguments = arguments;
        send.apply(this, arguments);
    };
})(XMLHttpRequest.prototype.send);

(function (open) {
    XMLHttpRequest.prototype.open = function () {
        const requestUrl = arguments[1];
        this.addEventListener("readystatechange", function () {
            if (this.readyState !== XMLHttpRequest.DONE) {
                return;
            }
            if (this.status === 0 || (this.status >= 200 && this.status < 400)) {
                let data = {};
                try {
                    data = JSON.parse(this.responseText);
                } catch (error) {
                    return;
                }

                let branchId = getBranchId(this);

                if (data.possessions != null) {
                    submitPossessions(data.possessions);
                }
                if (data.area != null) {
                    submitAreaData(data.area);
                }
                if (data.character != null && data.character.setting != null) {
                    submitSettingData(data.character.setting);
                }
                if (data.displayCards != null) {
                    submitOpportunitiesData(data.displayCards);
                }

                if (requestUrl === CHOOSE_BRANCH_URL) {
                    submitBranchOutcomeData(branchId, data);
                } else if (data.phase === PHASE_STORYLET_LIST) {
                    submitStoryletListData(data.storylets);
                } else if (data.phase === PHASE_STORYLET_VIEW) {
                    submitStoryletData(data.storylet);
                } else if (data.phase === PHASE_STORYLET_VIEW_ITEM) {
                    submitStoryletData(data.storylet, true);
                }
            }
        }, false);
        open.apply(this, arguments);
    };
})(XMLHttpRequest.prototype.open);
