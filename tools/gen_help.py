# -*- coding: utf-8 -*-
# Generator for scc-help.view.json.txt (the in-app Help & Guide popup).
# Accordion design: each process section has a "More info" toggle that expands a
# step-by-step walkthrough in place. One section open at a time (view.custom.openSection int).
# Edit the SECTIONS data below and re-run:  python tools/gen_help.py   (writes ignition/views/scc-help.view.json.txt)
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                        # repo root (tools/ -> ..)
OUT = os.path.join(ROOT, 'ignition', 'views', 'scc-help.view.json.txt')

# ---- palette (concrete hex only -- no theme tokens, per project rule 3) --------------------
DARK, ORANGE, WHITE, PAGE = '#1B212B', '#E87722', '#FFFFFF', '#F4F6F9'
MUTED, BORDER, DETAILBG = '#5B6675', '#E8ECF2', '#F8FAFC'
WARN, WARN_BG = '#B4620A', '#FBF1E4'

# ---- content ------------------------------------------------------------------------------
# Each expandable section: id, bar color, title, "when" line, steps [(action, detail)], warnings [str].
SECTIONS = [
	{
		'bar': ORANGE,
		'title': 'Station Rectification  (tab 1)',
		'when': "A station shows the wrong ComponentID, or you need to set / clear a station\'s Component ID 1 or 2, or re-pull its next work order.",
		'steps': [
			('Select a station', 'Filter by Area or use the search box above the table. The right "Selected Station" panel fills in with the live tag path, Component ID 1 & 2, and a boundary indicator.'),
			('Enter a Reason', 'Required. It is written verbatim to the SupervisorOverrideLog with your username and a timestamp.'),
			('Set or clear the ID', 'In the Component ID Rectification section, type the new ComponentID -- or leave the field blank to unassign it. Component ID 1 and Component ID 2 have their own field and Commit button.'),
			('Commit Change, then confirm', 'A confirmation dialog appears; confirm to write the tag. A toast reports the result as "before -> after".'),
			('Refresh Next Work Order', 'Under Run Schedule Options, re-pulls that station\'s next order from its owning backend (BE1 for Frame/Boom/Paint, BE2 for the rest).'),
		],
		'warnings': [
			'Blocked if the station is actively building (an assembly WIP order at Status 2). Clear the WIP first.',
			'To set an ID it must already exist in MachineConfig; unknown IDs are rejected.',
			'A mismatch banner appears when the scanned-in ID differs from the run schedule\'s next expected ID -- Refresh Next Work Order usually clears it.',
		],
	},
	{
		'bar': '#0C8599',
		'title': 'AMR Rectification  (tab 2)',
		'when': 'An AMR (mobile robot) is carrying the wrong ComponentID and needs corrected or cleared.',
		'steps': [
			('Find the AMR', 'Use the search box; the fleet table lists each AMR with its current Component ID 1 & 2.'),
			('Select it', 'The AMR Details panel shows that AMR\'s current Component ID 1 and Component ID 2.'),
			('Enter a Reason', 'Required; logged with your username.'),
			('Set or unassign', 'Component 1 and Component 2 have their own field + Commit button. Type the new ID, or leave it blank to unassign. Commit, then confirm.'),
			('Payload re-send', 'Every commit (set OR clear) re-sends the AMR payload to Navithor / the ACU (size profile + scanner) so the robot\'s profile matches. The toast notes whether the payload refresh succeeded.'),
		],
		'warnings': [
			'If the toast warns the payload refresh failed, verify the AMR\'s payload manually -- the ID itself still committed.',
			'The payload uses the AMR\'s existing itemNumber; if the size profile must change, make sure the itemNumber is right first.',
		],
	},
	{
		'bar': '#2F9E44',
		'title': 'Manual Assembly  (tab 3)',
		'when': 'You need to manually schedule whole-good serial(s) into the assembly line.',
		'steps': [
			('Add serials', 'Type a serial and click Add; repeat for each machine. They stack as rows.'),
			('Verify All', 'Each row turns green VERIFIED or red INVALID. Verify checks the serial exists in MachineConfig and is not already scheduled in Assembly.'),
			('Enter a Reason', 'Required; applied to every serial scheduled and logged.'),
			('Legacy toggle (if needed)', 'Turn on Legacy for legacy-line builds -- they enter at LL0010 instead of TF0010.'),
			('Schedule All', 'Schedules every valid serial via createAssemblyOrder on BE2. Invalid rows are skipped with a reason; the toast summarizes scheduled vs skipped.'),
		],
		'warnings': [
			'M-numbers (non-whole-good components) cannot be scheduled in Assembly.',
			'A serial that is already active (Scheduled / WIP / Associated) is skipped as a duplicate.',
		],
	},
	{
		'bar': '#E8920C',
		'title': 'Work Order Reconciliation  (tab 4)',
		'when': 'A machine\'s schedule / WIP status is wrong: mark a station Complete or WIP, or re-schedule a non-whole-good (M-number).',
		'steps': [
			('Search', 'Enter a ComponentID (M...) or a whole-good serial and Search.'),
			('View the entries', 'Toggle Rows (list) or Chart (flow); Full View opens the flow full-screen. For a whole good you also see the Associated Components panel (view-only).'),
			('Select a row, enter a Reason', 'Pick the station entry to act on and enter a Reason.'),
			('Mark Complete at Station', 'Sets Complete (Status 3), backfills the WIP timestamp if it was empty, runs the line/area completion cascade for a serial, and re-pulls that station\'s next work order.'),
			('Mark WIP', 'Sets the station to WIP (Status 2) + timestamp, then re-pulls the next work order. Blocked if the entry is already Complete.'),
			('NWG (M-number) scheduling', 'For an M-number: Schedule for Pre-Paint inserts a Status-1 fab row at the section\'s prepaint station; Pre-Assembly inserts at TF000X and closes out any active prepaint rows.'),
		],
		'warnings': [
			'An M-number that is aborted or non-conformanced is blocked from manual changes until it is resolved.',
			'If a screen looks stale after an action, use its Refresh button -- nothing polls on its own.',
		],
	},
	{
		'bar': '#6741D9',
		'title': 'Machine Overview  (Chart)',
		'when': 'You want to see where a machine is across the line and act on a specific station.',
		'steps': [
			('Open it', 'On Work Order Reconciliation, search a machine and switch to Chart (or Full View).'),
			('Read the flow', 'Each station is a node laid out by area / swimlane; the current WIP station glows orange.'),
			('Act on a node', 'Click a node to open its actions -- Mark WIP or Mark Complete (same effects as the Rows view).'),
		],
		'warnings': [
			'The chart is a read-only view of the schedule rows; every change still runs through the same audited actions.',
		],
	},
]

# Always-visible intro card (no toggle).
OVERVIEW = {
	'bar': DARK,
	'title': 'Overview',
	'when': 'Make authorized manual Station Control interventions without opening the Designer. Requires the Engineering, Supervisor, or Scheduler role.',
	'lines': [
		'Pick the tab for the tool you need, then click "More info" on any section below for a step-by-step walkthrough.',
		'Every action requires a Reason and is written to the SupervisorOverrideLog (user / type / before -> after / time). Commits are real production changes.',
	],
}

# Always-visible info + tips cards at the bottom (no toggle).
INFO_CARDS = [
	{
		'bar': MUTED,
		'title': 'Remember',
		'lines': [
			'Every commit needs a Reason and is logged to the SupervisorOverrideLog.',
			'Mark Complete / Mark WIP re-fire getNextWorkOrder for that station.',
			'If a screen looks stale after an action, use its Refresh button -- nothing auto-polls.',
			'Read the confirmation dialog before you approve it -- these are live production changes.',
		],
	},
]


# ---- component emitters -------------------------------------------------------------------
def label(name, text, style, grow=False):
	comp = {'type': 'ia.display.label', 'meta': {'name': name}, 'props': {'text': text, 'style': style}}
	comp['position'] = {'grow': 1, 'shrink': 1} if grow else {'basis': 'auto', 'shrink': 0}
	return comp


def bar(color):
	return {
		'type': 'ia.display.label', 'meta': {'name': 'Bar'},
		'props': {'text': '', 'style': {'width': '6px', 'height': '20px', 'borderRadius': '3px', 'backgroundColor': color}},
		'position': {'basis': '6px', 'shrink': 0},
	}


def title_label(text):
	return label('Title', text, {'color': DARK, 'fontSize': '16px', 'fontWeight': '800', 'letterSpacing': '0.3px', 'whiteSpace': 'normal'}, grow=True)


def when_label(text):
	return label('When', 'When:  ' + text, {'color': MUTED, 'fontSize': '13.5px', 'fontWeight': '500', 'lineHeight': '1.5', 'whiteSpace': 'normal'})


def plain_line(name, text):
	return label(name, text, {'color': DARK, 'fontSize': '13.5px', 'fontWeight': '400', 'lineHeight': '1.5', 'whiteSpace': 'normal'})


def more_info_button(idx):
	toggle = '\tself.view.custom.openSection = -1 if self.view.custom.openSection == {i} else {i}\n'.format(i=idx)
	return {
		'type': 'ia.input.button', 'meta': {'name': 'MoreInfo'},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {
			'text': 'More info',
			'style': {
				'backgroundColor': WHITE, 'color': MUTED, 'border': '1px solid ' + BORDER,
				'borderRadius': '8px', 'fontWeight': '700', 'fontSize': '12.5px', 'padding': '5px 12px',
				'whiteSpace': 'nowrap', 'overflow': 'hidden',
			},
			'image': {'icon': {'path': 'material/expand_more', 'color': MUTED, 'style': {'width': '16px', 'height': '16px', 'flexShrink': '0'}}},
		},
		'propConfig': {
			'props.text': {'binding': {'type': 'expr', 'config': {'expression': "if({view.custom.openSection} = " + str(idx) + ", 'Show less', 'More info')"}}},
			'props.image.icon.path': {'binding': {'type': 'expr', 'config': {'expression': "if({view.custom.openSection} = " + str(idx) + ", 'material/expand_less', 'material/expand_more')"}}},
		},
		'events': {'dom': {'onClick': {'type': 'script', 'scope': 'G', 'config': {'script': toggle}}}},
	}


def step_row(num, action, detail, accent):
	chip = {
		'type': 'ia.display.label', 'meta': {'name': 'Num'},
		'props': {'text': str(num), 'style': {
			'width': '22px', 'height': '22px', 'borderRadius': '11px', 'backgroundColor': accent,
			'color': WHITE, 'fontSize': '12px', 'fontWeight': '800', 'textAlign': 'center', 'lineHeight': '22px',
		}},
		'position': {'basis': '22px', 'shrink': 0},
	}
	textCol = {
		'type': 'ia.container.flex', 'meta': {'name': 'Txt'},
		'position': {'grow': 1, 'shrink': 1},
		'props': {'direction': 'column', 'style': {'gap': '1px', 'minWidth': '0px'}},
		'children': [
			label('Action', action, {'color': DARK, 'fontSize': '13.5px', 'fontWeight': '700', 'whiteSpace': 'normal', 'lineHeight': '1.45'}),
			label('Detail', detail, {'color': MUTED, 'fontSize': '13px', 'fontWeight': '400', 'whiteSpace': 'normal', 'lineHeight': '1.5'}),
		],
	}
	return {
		'type': 'ia.container.flex', 'meta': {'name': 'Step{}'.format(num)},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'row', 'alignItems': 'flex-start', 'style': {'gap': '10px'}},
		'children': [chip, textCol],
	}


def warning_row(idx, text):
	icon = {
		'type': 'ia.display.icon', 'meta': {'name': 'WIcon'},
		'position': {'basis': '16px', 'shrink': 0},
		'props': {'path': 'material/warning', 'color': WARN, 'style': {'width': '16px', 'height': '16px'}},
	}
	return {
		'type': 'ia.container.flex', 'meta': {'name': 'Warn{}'.format(idx)},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'row', 'alignItems': 'flex-start', 'style': {'gap': '8px'}},
		'children': [icon, label('WTxt', text, {'color': WARN, 'fontSize': '12.5px', 'fontWeight': '500', 'whiteSpace': 'normal', 'lineHeight': '1.45'}, grow=True)],
	}


def details_panel(idx, section):
	children = [label('StepsHdr', 'STEP BY STEP', {'color': DARK, 'fontSize': '11px', 'fontWeight': '800', 'letterSpacing': '0.7px'})]
	for n, (action, detail) in enumerate(section['steps'], start=1):
		children.append(step_row(n, action, detail, section['bar']))
	if section.get('warnings'):
		children.append(label('WarnHdr', 'WATCH OUT', {'color': WARN, 'fontSize': '11px', 'fontWeight': '800', 'letterSpacing': '0.7px', 'paddingTop': '2px'}))
		for wi, w in enumerate(section['warnings']):
			children.append(warning_row(wi, w))
	panel = {
		'type': 'ia.container.flex', 'meta': {'name': 'Details'},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'column', 'style': {
			'backgroundColor': DETAILBG, 'border': '1px solid ' + BORDER, 'borderRadius': '8px',
			'padding': '12px 14px', 'gap': '11px', 'marginTop': '4px',
		}},
		'children': children,
	}
	panel['propConfig'] = {'position.display': {'binding': {'type': 'expr', 'config': {'expression': '{view.custom.openSection} = ' + str(idx)}}}}
	return panel


CARD_STYLE = {
	'backgroundColor': WHITE, 'border': '1px solid ' + BORDER, 'borderRadius': '10px',
	'padding': '14px 16px', 'gap': '9px', 'boxShadow': '0 1px 2px rgba(27,33,43,0.05)',
}


def header_row(section, toggle_idx=None):
	kids = [bar(section['bar']), title_label(section['title'])]
	if toggle_idx is not None:
		kids.append(more_info_button(toggle_idx))
	return {
		'type': 'ia.container.flex', 'meta': {'name': 'Hdr'},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'row', 'alignItems': 'center', 'style': {'gap': '10px'}},
		'children': kids,
	}


def accordion_card(idx, section):
	return {
		'type': 'ia.container.flex', 'meta': {'name': 'Sec{}'.format(idx)},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'column', 'style': CARD_STYLE},
		'children': [header_row(section, toggle_idx=idx), when_label(section['when']), details_panel(idx, section)],
	}


def static_card(name, section):
	kids = [header_row(section)]
	if section.get('when'):
		kids.append(when_label(section['when']))
	for li, line in enumerate(section.get('lines', [])):
		kids.append(plain_line('Line{}'.format(li), line))
	return {
		'type': 'ia.container.flex', 'meta': {'name': name},
		'position': {'basis': 'auto', 'shrink': 0},
		'props': {'direction': 'column', 'style': CARD_STYLE},
		'children': kids,
	}


# ---- header bar (dark, matches the rest of the SCC) ---------------------------------------
def header_bar():
	return {
		'type': 'ia.container.flex', 'meta': {'name': 'HeaderBar'},
		'position': {'basis': '64px', 'shrink': 0},
		'props': {'direction': 'row', 'alignItems': 'center', 'style': {
			'backgroundColor': DARK, 'padding': '14px 22px', 'gap': '14px', 'borderBottom': '3px solid ' + ORANGE,
		}},
		'children': [
			{'type': 'ia.display.icon', 'meta': {'name': 'Icon'}, 'position': {'basis': '24px', 'shrink': 0},
			 'props': {'path': 'material/help_outline', 'color': ORANGE, 'style': {'width': '24px', 'height': '24px'}}},
			label('Title', 'Station Control Center  -  Help & Guide',
				  {'color': WHITE, 'fontSize': '18px', 'fontWeight': '700', 'letterSpacing': '0.3px',
				   'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}, grow=True),
			{'type': 'ia.input.button', 'meta': {'name': 'Close_Button'}, 'position': {'basis': 'auto', 'shrink': 0},
			 'props': {'text': 'Close', 'style': {
				 'backgroundColor': '#2A3340', 'color': WHITE, 'border': '1px solid ' + MUTED, 'borderRadius': '8px',
				 'fontWeight': '600', 'fontSize': '14px', 'padding': '9px 16px', 'overflow': 'hidden', 'whiteSpace': 'nowrap'},
				 'image': {'icon': {'path': 'material/close', 'color': WHITE, 'style': {'width': '18px', 'height': '18px', 'flexShrink': '0'}}}},
			 'events': {'dom': {'onClick': {'type': 'script', 'scope': 'G', 'config': {'script': "\tsystem.perspective.closePopup('sccHelp')\n"}}}}},
		],
	}


def build():
	body_children = [static_card('Sec0', OVERVIEW)]
	for i, section in enumerate(SECTIONS, start=1):        # accordion sections use idx 1..N (0 = overview, never a toggle)
		body_children.append(accordion_card(i, section))
	for ci, card in enumerate(INFO_CARDS):
		body_children.append(static_card('Info{}'.format(ci), card))

	body = {
		'type': 'ia.container.flex', 'meta': {'name': 'Body'},
		'position': {'grow': 1, 'shrink': 1},
		'props': {'direction': 'column', 'style': {
			'backgroundColor': PAGE, 'padding': '18px 20px', 'gap': '12px', 'overflow': 'auto', 'minHeight': '0px'}},
		'children': body_children,
	}
	view = {
		'custom': {'openSection': -1},
		'params': {},
		'props': {'defaultSize': {'width': 720, 'height': 820}},
		'root': {
			'type': 'ia.container.flex', 'meta': {'name': 'root'},
			'props': {'direction': 'column', 'style': {
				'backgroundColor': WHITE, 'height': '100%', 'overflow': 'hidden',
				'borderRadius': '12px', 'boxShadow': '0 12px 40px rgba(0,0,0,0.30)'}},
			'children': [header_bar(), body],
		},
	}
	return view


if __name__ == '__main__':
	with open(OUT, 'w', encoding='utf-8') as fh:
		fh.write(json.dumps(build(), indent=2))
		fh.write('\n')
	print('wrote ' + OUT)
