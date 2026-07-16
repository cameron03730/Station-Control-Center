# STASH — Boom-sub (TB) association editing feature (removed 2026-07-01, session 11e)

the user asked to strip the **association EDITING** logic out of the SCC for now (too many test cases)
and to let **TB stations be marked complete with NO boundary**. Associations are still **DISPLAYED**
(read-only) on the Work Order Reconciliation tab; only the create/edit/clear (associate) paths were removed.

This folder is the complete stash to bring it back later. Nothing here is imported/deployed while it lives
in `_stash_association_TB/`.

## What was removed
- **`scc-associate-popup.view.json.txt`** — the associate/clear modal. MOVED here intact.
- **`scc-card-assoc`** — the 3 action buttons (Associate / Edit / Clear) were stripped; the card is now
  display-only (section badge + componentID). See "scc-card-assoc buttons" below to restore them.
- **`scc-node-action`** — the `BoomAssoc` section (+ `custom.assocInfo` binding + `sccAssocDone` handler)
  was removed. See below.
- **`work-order-reconciliation`** — the `sccAssocDone` message handler was removed; the `AssocLbl` text
  changed from "(Edit fills an empty boom section)" back to a plain label.
- **`StationControl.SCC` code.py** — the functions/consts below were removed, plus the TB guard in
  `markSerialComplete`, plus 3 `runAction` dispatch keys.

## Restore checklist
1. Move `scc-associate-popup.view.json.txt` back to `files/`.
2. In `_rebuild_zip.py`: remove `'scc-associate-popup'` from the `DROP` set, and add it back to
   `NEW_EMBEDDED` (and it's already in `FOLDER_TXT`).
3. Re-add the code.py block (below) after `getMachineFlow`, re-add the `markSerialComplete` TB guard,
   re-add the 3 `runAction` keys.
4. Re-add the `scc-card-assoc` buttons, the `scc-node-action` BoomAssoc section, and the WO-recon
   `sccAssocDone` handler (all below).
5. Re-run `_validate_scc.py` + `_rebuild_zip.py`.

---

## code.py — removed block (paste back after `getMachineFlow` / `FLOW_LANE_ORDER`)

```python
BOOM_SUB_SECTIONS = {'TB0100': 'Fly', 'TB0500': 'InnerMid', 'TB0900': 'OuterMid', 'TB1600': 'Base'}


def boomSubItemName(station):
	'''
	Boom Sub station -> boom section ItemName (Fly/InnerMid/OuterMid/Base). Reuses the FE
	resolver RunSchedule.Assembly.getBoomSubItemName, falling back to BOOM_SUB_SECTIONS.
	Returns '' if not a known boom sub station.
	'''
	stn = (station or '').strip().upper()
	try:
		nm = RunSchedule.Assembly.getBoomSubItemName(stn)
		if nm:
			return nm
	except:
		pass
	return BOOM_SUB_SECTIONS.get(stn, '')


def nwgAssociations(serial):
	'''
	{ItemName: ComponentID} of the NWGs associated to a WG serial (BE getNwgAssociatedItems).
	Placeholder rows from insertUnAssignedAssociationForSerialNumber come back as 'UNASSIGNED'.
	Returns an empty dict on error / none found.
	'''
	try:
		return beExec('JcCommonOperations.getNwgAssociatedItems', {'serialNumber': serial}) or {}
	except:
		return {}


def isBoomAssociated(serial, section):
	'''True if the serial has a REAL (non-UNASSIGNED) NWG associated for the boom section.'''
	comp = (nwgAssociations(serial) or {}).get(section)
	if comp is None:
		return False
	return str(comp).strip().upper() not in ('', 'UNASSIGNED', 'NONE', 'NULL')


def validateBoomForAssociation(componentID):
	'''
	An NWG boom can be associated to a whole good only if it is (a) an M-number, (b) scheduled at
	TF000X (pre-assembly) with a ScheduledTimestamp, and (c) not already associated to a whole good.
	'''
	comp = (componentID or '').strip()
	if not comp:
		return {'ok': False, 'message': 'Enter an M-number to associate.'}
	if not comp.upper().startswith('M'):
		return {'ok': False, 'message': '{} is not an NWG (M-number).'.format(comp)}
	# (c) Not already associated to a whole good.
	try:
		existing = beExec('StationControl.findSerialNumber.findSerialNumber', {'NWGComponentID': comp})
	except:
		existing = None
	if existing is not None and str(existing).strip().upper() not in ('', 'UNASSIGNED', 'NONE', 'NULL'):
		return {'ok': False, 'message': '{} is already associated to {}.'.format(comp, existing)}
	# (b) Scheduled at TF000X (pre-assembly) with a scheduled timestamp.
	scheduled = False
	for r in (getScheduleEntries(comp) or []):
		if str(r.get('Station') or '').upper() == PREASSEMBLY_STATION and r.get('ScheduledTimestamp') is not None:
			scheduled = True
			break
	if not scheduled:
		return {'ok': False, 'message': '{} is not scheduled at {} with a scheduled timestamp.'.format(comp, PREASSEMBLY_STATION)}
	return {'ok': True, 'message': '{} is eligible to associate.'.format(comp)}


# Reverse of BOOM_SUB_SECTIONS: boom section -> a representative TB station (for the audit StationName).
BOOM_SECTION_STATIONS = {'Fly': 'TB0100', 'InnerMid': 'TB0500', 'OuterMid': 'TB0900', 'Base': 'TB1600'}


def associateBoomBySection(serial, section, componentID, reason, session):
	'''
	Core boom association: validate the NWG (validateBoomForAssociation), then reuse the existing BE
	upsertNwgToWgAssoc to set the WG<->NWG association for a boom SECTION (updates the UNASSIGNED
	placeholder row's ComponentID, or inserts). Used by both the list (WO-recon) and the grid (node popup).
	'''
	serial = (serial or '').strip()
	section = (section or '').strip()
	comp = (componentID or '').strip()
	reason = (reason or '').strip()
	if not serial:
		return {'ok': False, 'message': 'No serial supplied; search a serial first.'}
	if not section:
		return {'ok': False, 'message': 'No boom section supplied.'}
	if not reason:
		return {'ok': False, 'message': 'A reason is required.'}
	chk = validateBoomForAssociation(comp)
	if not chk['ok']:
		return chk
	beQuery('RunSchedule/insert/upsertNwgToWgAssoc', {'serialNumber': serial, 'itemName': section, 'componentID': comp})
	logStation = BOOM_SECTION_STATIONS.get(section, 'TF000X')
	logOverride(logStation, 'Boom Sub Associate', '{} ({}) associated to {}'.format(comp, section, serial), reason, getOverrideUser(session))
	return {'ok': True, 'message': '{} associated as the {} boom for {}.'.format(comp, section, serial)}


def associateBoomToSerial(serial, station, componentID, reason, session):
	'''Station-based wrapper for associateBoomBySection: resolves the boom section from the TB station first.'''
	section = boomSubItemName(station)
	if not section:
		return {'ok': False, 'message': '{} is not a boom sub station.'.format(station)}
	return associateBoomBySection(serial, section, componentID, reason, session)


def clearBoomAssociation(serial, section, reason, session):
	'''
	Un-associates a boom section (mirrors associateBoomBySection above). Requires the section to
	currently be associated, then reuses the same BE upsertNwgToWgAssoc with componentID='UNASSIGNED'.
	'''
	serial = (serial or '').strip()
	section = (section or '').strip()
	reason = (reason or '').strip()
	if not serial:
		return {'ok': False, 'message': 'No serial supplied; search a serial first.'}
	if not section:
		return {'ok': False, 'message': 'No boom section supplied.'}
	if not reason:
		return {'ok': False, 'message': 'A reason is required.'}
	if not isBoomAssociated(serial, section):
		return {'ok': False, 'message': '{} has no NWG associated to the {} boom; nothing to clear.'.format(serial, section)}
	beQuery('RunSchedule/insert/upsertNwgToWgAssoc', {'serialNumber': serial, 'itemName': section, 'componentID': 'UNASSIGNED'})
	logStation = BOOM_SECTION_STATIONS.get(section, 'TF000X')
	logOverride(logStation, 'Boom Sub Unassociate', '{} boom unassociated from {}'.format(section, serial), reason, getOverrideUser(session))
	return {'ok': True, 'message': '{} boom unassociated from {}.'.format(section, serial)}


def sectionAssociationForStation(serial, station):
	'''
	The current association state of a boom-sub station's section, for the Machine Overview node popup.
	Returns {'isBoomSub':bool, 'section':str, 'comp':str, 'unassigned':bool}.
	'''
	section = boomSubItemName(station)
	if not section:
		return {'isBoomSub': False, 'section': '', 'comp': '', 'unassigned': True}
	comp = (nwgAssociations(serial) or {}).get(section)
	un = (comp is None) or (str(comp).strip().upper() in ('', 'UNASSIGNED', 'NONE', 'NULL'))
	return {'isBoomSub': True, 'section': section, 'comp': ('' if un else str(comp)), 'unassigned': un}
```

## code.py — `markSerialComplete` TB guard (paste back at the top of the function, after the reason check)

```python
	# Boom Sub (TB*) guard: a boom sub station cannot be completed unless its boom section
	# (Fly/InnerMid/OuterMid/Base) has a REAL NWG associated to this serial (not UNASSIGNED).
	if (station or '').strip().upper().startswith('TB'):
		section = boomSubItemName(station)
		if not isBoomAssociated(serialNumber, section):
			label = section or 'boom sub'
			return {'ok': False, 'needsConfirm': False, 'message': 'Cannot complete {} - no NWG {} boom is associated to {}. Associate the {} boom first.'.format(station, label, serialNumber, label)}
```

## code.py — `runAction` dispatch keys (paste back into runAction)

```python
	if key == 'associateBoom':
		return associateBoomToSerial(a.get('serial'), a.get('station'), a.get('componentID'), a.get('reason', ''), session)
	if key == 'associateBoomBySection':
		return associateBoomBySection(a.get('serial'), a.get('section'), a.get('componentID'), a.get('reason', ''), session)
	if key == 'clearBoomAssociation':
		return clearBoomAssociation(a.get('serial'), a.get('section'), a.get('reason', ''), session)
```

## scc-card-assoc — the 3 action buttons (append back into root.children after `CompVal`)
The read-only card keeps `SectionBadge` + `CompVal`. To restore editing, re-add these three `ia.input.button`
children (params `serial`, `section`, `comp`, `unassigned` are still on the card):
- **AssociateBtn** — `position.display` = `{view.params.unassigned}`, opens `sccAssociate` with `{serial, section, comp}`.
- **EditBtn** — `position.display` = `!{view.params.unassigned}`, opens `sccAssociate` with `{serial, section, comp}`.
- **ClearBtn** — `position.display` = `!{view.params.unassigned}`, opens `sccAssociate` with `{serial, section, comp, 'mode':'clear'}`.
(Full JSON for the three buttons is in git history / the pre-11e zip backup `_backup_predeploy_*`; they open
`Plant Overview/Engineering/Station Control Center/embedded/scc-associate-popup`.)

## scc-node-action — BoomAssoc (restore)
Re-add: `custom.assocInfo` (expr-struct {serial: params.idText, station: params.station} → script transform
`StationControl.SCC.sectionAssociationForStation(serial, station)`); the `BoomAssoc` flex section (shown via
`position.display` = `{view.custom.assocInfo.isBoomSub}`) with the section label, the green/red comp value, and
the Associate/Edit button opening `sccAssociate`; and the `sccAssocDone` message handler
(`closePopup sccProgress` + `closePopup sccAssociate` + `refreshBinding custom.assocInfo`).

## work-order-reconciliation — sccAssocDone handler (restore)
```
messageType: sccAssocDone (sessionScope) ->
	system.perspective.closePopup('sccProgress')
	system.perspective.closePopup('sccAssociate')
	toast payload.message
	re-run: self.view.custom.componentInfo = StationControl.SCC.lookupComponent((self.view.custom.searchText or '').strip())
```
And restore `AssocLbl` text to: "ASSOCIATED COMPONENTS  (Edit fills an empty boom section)".
