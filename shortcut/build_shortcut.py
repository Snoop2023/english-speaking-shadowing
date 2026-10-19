#!/usr/bin/env python3
"""Generate 英语随机刷.shortcut — pick 10 random clips from the album and swipe through them.

The album name must match exactly (full-width ｜ and en dash –), because the
shortcut looks it up by name.

    python3 shortcut/build_shortcut.py   # -> shortcut/英语随机刷.shortcut
"""
import plistlib
import uuid
from pathlib import Path

ALBUM = "英语素材｜由浅入深｜001–198"
OUT = Path(__file__).resolve().parent / "英语随机刷.shortcut"


def enum(v):
    return {"Enumeration": {"Value": v, "WFSerializationType": "WFStringSubstitutableState"}}


find_uuid = str(uuid.uuid4()).upper()
actions = [
    {   # find photos: album = 英语素材, media type = video, random order, limit 10
        "WFWorkflowActionIdentifier": "is.workflow.actions.filter.photos",
        "WFWorkflowActionParameters": {
            "UUID": find_uuid,
            "WFContentItemFilter": {
                "Value": {
                    "WFActionParameterFilterPrefix": 1,
                    "WFContentPredicateBoundedDate": False,
                    "WFActionParameterFilterTemplates": [
                        {"Operator": 4, "Property": "Album", "Removable": True, "Values": enum(ALBUM)},
                        {"Operator": 4, "Property": "Media Type", "Removable": True, "Values": enum("Video")},
                    ],
                },
                "WFSerializationType": "WFContentPredicateTableTemplate",
            },
            "WFContentItemSortProperty": "Random",
            "WFContentItemLimitEnabled": True,
            "WFContentItemLimitNumber": 10.0,
        },
    },
    {   # quick look: swipe left/right to hear each one
        "WFWorkflowActionIdentifier": "is.workflow.actions.previewdocument",
        "WFWorkflowActionParameters": {
            "WFInput": {
                "Value": {"OutputUUID": find_uuid, "OutputName": "照片", "Type": "ActionOutput"},
                "WFSerializationType": "WFTextTokenAttachment",
            }
        },
    },
]

wf = {
    "WFWorkflowClientVersion": "2607.0.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 463140863, "WFWorkflowIconGlyphNumber": 59511},
    "WFWorkflowImportQuestions": [],
    "WFWorkflowInputContentItemClasses": [],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowTypes": [],
    "WFWorkflowHasShortcutInputVariables": False,
    "WFQuickActionSurfaces": [],
    "WFWorkflowActions": actions,
}

with OUT.open("wb") as f:
    plistlib.dump(wf, f, fmt=plistlib.FMT_BINARY)
print(f"wrote {OUT}")
