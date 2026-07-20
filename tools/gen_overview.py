# -*- coding: utf-8 -*-
# Generator for the Machine Overview flow views. Emits TWO files:
#   scc-flow-canvas.view.json.txt  -- reusable content-only canvas (legend + 11 swimlanes of
#       scc-flow-node). Reactively fetches flowRows from its own idText param. Embedded BOTH
#       inline on the Work Order Reconciliation tab (Chart toggle) AND inside the scc-overview popup.
#   scc-overview.view.json.txt     -- full-screen popup shell (dark header + embedded canvas);
#       kept as the Station Rectification "Overview" launcher.
# All concrete hex (no theme tokens). Ignition expression equality uses '=' (single).
import json, os

EMB = "Plant Overview/Engineering/Station Control Center/embedded/"

# Must match StationControl.SCC.FLOW_LANE_ORDER exactly.
LANES = ['Frame Fab', 'Boom Fab', 'Paint', 'Pre-Assembly', 'Main Line',
         'Legacy', 'Boom Sub', 'Cab Sub', 'Engine Sub', 'Outrigger Sub', 'Other']

ACCENT = {
    'Frame Fab': '#E87722', 'Boom Fab': '#E8920C', 'Paint': '#0C8599',
    'Pre-Assembly': '#6741D9', 'Main Line': '#1B212B', 'Legacy': '#5B6675',
    'Boom Sub': '#2F9E44', 'Cab Sub': '#2F9E44', 'Engine Sub': '#2F9E44',
    'Outrigger Sub': '#2F9E44', 'Other': '#5B6675',
}


def sanit(area):
    return area.replace(' ', '').replace('-', '')


# ---------- legend ----------
def legend_chip(text, color):
    return {
        "type": "ia.container.flex", "meta": {"name": "Lg" + sanit(text)},
        "position": {"basis": "auto", "shrink": 0},
        "props": {"direction": "row", "alignItems": "center", "style": {"gap": "6px"}},
        "children": [
            {"type": "ia.display.label", "meta": {"name": "Dot"},
             "position": {"basis": "11px", "shrink": 0},
             "props": {"text": "", "style": {"width": "11px", "height": "11px", "borderRadius": "999px",
                                             "backgroundColor": color, "boxShadow": "0 1px 2px rgba(27,33,43,0.18)"}}},
            {"type": "ia.display.label", "meta": {"name": "Txt"},
             "position": {"basis": "auto", "shrink": 0},
             "props": {"text": text, "style": {"color": "#5B6675", "fontSize": "11px", "fontWeight": "700",
                                              "letterSpacing": "0.4px", "whiteSpace": "nowrap"}}},
        ],
    }


legend_bar = {
    "type": "ia.container.flex", "meta": {"name": "LegendBar"},
    "position": {"basis": "auto", "shrink": 0},
    "props": {"direction": "row", "alignItems": "center", "wrap": "wrap",
              "style": {"backgroundColor": "#FFFFFF", "border": "1px solid #E8ECF2", "borderRadius": "10px",
                        "padding": "10px 16px", "gap": "18px", "boxShadow": "0 1px 2px rgba(27,33,43,0.04)"}},
    "children": [
        legend_chip("SCHEDULED", "#E8920C"),
        legend_chip("WIP", "#E87722"),
        legend_chip("COMPLETE", "#2F9E44"),
        legend_chip("ASSOC", "#0C8599"),
        legend_chip("ABORT / NON-CONF", "#E03131"),
        {"type": "ia.display.label", "meta": {"name": "Hint"},
         "position": {"grow": 1, "shrink": 1},
         "props": {"text": "Click a station to mark it WIP or Complete.",
                   "style": {"color": "#9AA3B0", "fontSize": "12px", "fontWeight": "500",
                             "textAlign": "right", "whiteSpace": "nowrap"}}},
    ],
}


# ---------- one swimlane ----------
def lane(area):
    s = sanit(area)
    has_rows_xf = "\treturn any((str((r or {}).get('Area')) == '%s') for r in (value or []))\n" % area
    count_xf = ("\tn = 0\n\tfor r in (value or []):\n\t\tif str((r or {}).get('Area')) == '%s':\n\t\t\tn += 1\n"
                "\treturn str(n) + (' station' if n == 1 else ' stations')\n") % area
    inst_xf = ("\tout = []\n\tfor r in (value or []):\n\t\tif str((r or {}).get('Area')) != '%s':\n\t\t\tcontinue\n"
               "\t\tout.append({'rowData': dict(r), 'idText': self.view.params.idText, 'isNWG': self.view.params.isNWG, 'idx': len(out)})\n"
               "\treturn out\n") % area
    header = {
        "type": "ia.container.flex", "meta": {"name": "Hdr" + s},
        "position": {"basis": "auto", "shrink": 0},
        "props": {"direction": "row", "alignItems": "center",
                  "style": {"gap": "10px", "paddingBottom": "2px"}},
        "children": [
            {"type": "ia.display.label", "meta": {"name": "Accent"},
             "position": {"basis": "5px", "shrink": 0},
             "props": {"text": "", "style": {"width": "5px", "height": "18px", "borderRadius": "3px",
                                            "backgroundColor": ACCENT[area]}}},
            {"type": "ia.display.label", "meta": {"name": "Name"},
             "position": {"basis": "auto", "shrink": 0},
             "props": {"text": area.upper(), "style": {"color": "#1B212B", "fontSize": "12.5px", "fontWeight": "800",
                                                      "letterSpacing": "0.7px", "whiteSpace": "nowrap"}}},
            {"type": "ia.display.label", "meta": {"name": "Count"},
             "position": {"basis": "auto", "shrink": 0},
             "props": {"text": "", "style": {"color": "#8A929E", "fontSize": "11px", "fontWeight": "700",
                                            "backgroundColor": "#EEF1F5", "borderRadius": "999px",
                                            "padding": "2px 10px", "whiteSpace": "nowrap"}},
             "propConfig": {"props.text": {"binding": {"type": "property",
                 "config": {"path": "view.custom.flowRows"}, "transforms": [{"type": "script", "code": count_xf}]}}}},
            {"type": "ia.display.label", "meta": {"name": "Rule"},
             "position": {"grow": 1, "shrink": 1},
             "props": {"text": "", "style": {"borderTop": "1px solid #E8ECF2", "margin": "0 0 0 4px"}}},
        ],
    }
    repeater = {
        "type": "ia.display.flex-repeater", "meta": {"name": "Rep" + s},
        "position": {"basis": "auto", "shrink": 0},
        "props": {"path": EMB + "scc-flow-node", "direction": "row", "wrap": "wrap",
                  "style": {"gap": "10px 0px"}},
        "propConfig": {"props.instances": {"binding": {"type": "property",
            "config": {"path": "view.custom.flowRows"}, "transforms": [{"type": "script", "code": inst_xf}]}}},
    }
    return {
        "type": "ia.container.flex", "meta": {"name": "Lane" + s},
        "position": {"basis": "auto", "shrink": 0},
        "props": {"direction": "column", "style": {"gap": "10px"}},
        "propConfig": {"position.display": {"binding": {"type": "property",
            "config": {"path": "view.custom.flowRows"}, "transforms": [{"type": "script", "code": has_rows_xf}]}}},
        "children": [header, repeater],
    }


empty_hint = {
    "type": "ia.display.label", "meta": {"name": "EmptyHint"},
    "position": {"grow": 1, "shrink": 1},
    "props": {"text": "No schedule entries found for this machine.",
              "style": {"color": "#9AA3B0", "fontSize": "15px", "fontWeight": "500",
                        "textAlign": "center", "padding": "56px 8px"}},
    "propConfig": {"position.display": {"binding": {"type": "property",
        "config": {"path": "view.custom.flowRows"}, "transforms": [{"type": "script", "code": "\treturn not bool(value)\n"}]}}},
}


# ================= scc-flow-canvas (reusable content view) =================
flowrows_xf = ("\tval = (value or '')\n\ttry:\n\t\tval = val.strip()\n\texcept:\n\t\tpass\n"
               "\tif not val:\n\t\treturn []\n\ttry:\n\t\treturn StationControl.SCC.getMachineFlow(val)\n\texcept:\n\t\treturn []\n")

canvas_done = ("\tsystem.perspective.closePopup('sccProgress')\n\tsystem.perspective.closePopup('sccNodeAction')\n"
               "\tok = payload.get('ok', False)\n\tmsg = payload.get('message', '')\n\tif msg:\n"
               "\t\tsystem.perspective.openPopup('sccToast', 'Plant Overview/Engineering/Station Control Center/embedded/scc-toast-popup', {'msg': msg, 'error': not ok}, showCloseIcon=False, modal=True)\n"
               "\tself.view.refreshBinding('custom.flowRows')\n")

canvas_refresh = "\tself.view.refreshBinding('custom.flowRows')\n"

canvas = {
    "custom": {"flowRows": []},
    "params": {"idText": "", "isNWG": False},
    "propConfig": {
        "params.idText": {"paramDirection": "input", "persistent": True},
        "params.isNWG": {"paramDirection": "input", "persistent": True},
        "custom.flowRows": {"binding": {"type": "property", "config": {"path": "view.params.idText"},
            "transforms": [{"type": "script", "code": flowrows_xf}]}},
    },
    "props": {"defaultSize": {"width": 1240, "height": 760}},
    "root": {
        "type": "ia.container.flex", "meta": {"name": "root"},
        "position": {"grow": 1, "shrink": 1},
        "props": {"direction": "column", "style": {"backgroundColor": "#F7F9FC", "borderRadius": "10px",
                  "padding": "16px", "gap": "16px", "overflow": "auto", "height": "100%"}},
        "children": [legend_bar] + [lane(a) for a in LANES] + [empty_hint],
        "scripts": {"customMethods": [], "extensionFunctions": None, "messageHandlers": [
            {"messageType": "sccOverviewDone", "pageScope": False, "sessionScope": True, "viewScope": False,
             "script": canvas_done},
            {"messageType": "sccFlowRefresh", "pageScope": False, "sessionScope": True, "viewScope": False,
             "script": canvas_refresh},
        ]},
    },
}


# ================= scc-overview (popup shell embedding the canvas) =================
def hdr_btn(name, text, icon, onclick):
    return {
        "type": "ia.input.button", "meta": {"name": name},
        "position": {"basis": "auto", "shrink": 0},
        "props": {"text": text, "style": {"backgroundColor": "#2A3340", "color": "#FFFFFF",
                  "border": "1px solid #5B6675", "borderRadius": "8px", "fontWeight": "600", "fontSize": "14px",
                  "padding": "9px 16px", "overflow": "hidden", "whiteSpace": "nowrap"},
                  "image": {"icon": {"path": icon, "color": "#FFFFFF",
                            "style": {"width": "18px", "height": "18px", "flexShrink": "0"}}}},
        "events": {"dom": {"onClick": {"type": "script", "scope": "G", "config": {"script": onclick}}}},
    }


header_bar = {
    "type": "ia.container.flex", "meta": {"name": "HeaderBar"},
    "position": {"basis": "64px", "shrink": 0},
    "props": {"direction": "row", "alignItems": "center",
              "style": {"backgroundColor": "#1B212B", "padding": "12px 22px", "gap": "16px",
                        "borderBottom": "3px solid #E87722"}},
    "children": [
        {"type": "ia.display.icon", "meta": {"name": "TitleIcon"},
         "position": {"basis": "24px", "shrink": 0},
         "props": {"path": "material/account_tree", "color": "#E87722", "style": {"width": "24px", "height": "24px"}}},
        {"type": "ia.display.label", "meta": {"name": "TitleLbl"},
         "position": {"basis": "auto", "shrink": 0},
         "props": {"text": "MACHINE OVERVIEW", "style": {"color": "#FFFFFF", "fontSize": "18px",
                   "fontWeight": "700", "letterSpacing": "0.4px", "whiteSpace": "nowrap"}}},
        {"type": "ia.display.label", "meta": {"name": "IdLbl"},
         "position": {"basis": "auto", "shrink": 1},
         "props": {"text": "", "style": {"color": "#A7B0BE", "fontSize": "15px", "fontWeight": "600",
                   "fontFamily": "'SF Mono','Roboto Mono',Consolas,monospace", "whiteSpace": "nowrap",
                   "overflow": "hidden", "textOverflow": "ellipsis"}},
         "propConfig": {"props.text": {"binding": {"type": "expr",
             "config": {"expression": "coalesce({view.params.idText}, '--')"}}}}},
        {"type": "ia.display.label", "meta": {"name": "TypePill"},
         "position": {"basis": "auto", "shrink": 0},
         "props": {"text": "", "style": {"color": "#FFFFFF", "fontSize": "11.5px", "fontWeight": "700",
                   "letterSpacing": "0.5px", "borderRadius": "999px", "padding": "4px 13px",
                   "whiteSpace": "nowrap", "backgroundColor": "#E87722"}},
         "propConfig": {
             "props.text": {"binding": {"type": "expr",
                 "config": {"expression": "if({view.params.isNWG}, 'NON-WHOLE GOOD', 'WHOLE GOOD')"}}},
             "props.style.backgroundColor": {"binding": {"type": "expr",
                 "config": {"expression": "if({view.params.isNWG}, '#0C8599', '#E87722')"}}}}},
        {"type": "ia.display.label", "meta": {"name": "Spacer"},
         "position": {"grow": 1, "shrink": 1}, "props": {"text": "", "style": {}}},
        hdr_btn("Refresh_Button", "Refresh", "material/refresh",
                "\tsystem.perspective.sendMessage('sccFlowRefresh', payload={}, scope='session')\n"),
        hdr_btn("Close_Button", "Close", "material/close",
                "\tsystem.perspective.closePopup('sccOverview')\n"),
    ],
}

canvas_host = {
    "type": "ia.display.view", "meta": {"name": "CanvasHost"},
    "position": {"grow": 1, "shrink": 1},
    "props": {"path": EMB + "scc-flow-canvas", "params": {"idText": "", "isNWG": False}},
    "propConfig": {
        "props.params.idText": {"binding": {"type": "expr", "config": {"expression": "coalesce({view.params.idText}, '')"}}},
        "props.params.isNWG": {"binding": {"type": "expr", "config": {"expression": "{view.params.isNWG}"}}},
    },
}

overview = {
    "custom": {},
    "params": {"idText": "", "isNWG": False},
    "propConfig": {
        "params.idText": {"paramDirection": "input", "persistent": True},
        "params.isNWG": {"paramDirection": "input", "persistent": True},
    },
    "props": {"defaultSize": {"width": 1500, "height": 920}},
    "root": {
        "type": "ia.container.flex", "meta": {"name": "root"},
        "props": {"direction": "column", "style": {"backgroundColor": "#F4F6F9", "height": "100%",
                  "overflow": "hidden"}},
        "children": [header_bar, canvas_host],
    },
}


def write(name, obj):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tools/ -> repo root
    out = os.path.join(root, 'ignition', 'views', name)
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2)
        fh.write('\n')
    print('wrote ' + name)


write('scc-flow-canvas.view.json.txt', canvas)
write('scc-overview.view.json.txt', overview)
