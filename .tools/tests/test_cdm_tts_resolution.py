"""Regression checks for Cooldown Manager TTS text-key resolution."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CdmTtsResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.focus = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_FocusKick.lua").read_text()
        cls.cdm_main = (ROOT / "EllesmereUICooldownManager" / "EllesmereUICooldownManager.lua").read_text()
        cls.fake_active = (ROOT / "EllesmereUICooldownManager" / "EllesmereUICdmFakeActive.lua").read_text()
        cls.watch = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookIconWatch.lua").read_text()
        cls.icons = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_Icons.lua").read_text()
        cls.store = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_Store.lua").read_text()
        cls.tracked = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_BuffBarAssign.lua").read_text()
        cls.custom_buffs = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookCustomBuffs.lua").read_text()
        cls.options = (ROOT / "EllesmereUIOptions" / "CooldownManager_Options" / "SpellPicker_Options.lua").read_text()
        cls.buff_page = (ROOT / "EllesmereUIOptions" / "CooldownManager_Options" / "BuffBarsPage_Options.lua").read_text()
        cls.bars_page = (ROOT / "EllesmereUIOptions" / "CooldownManager_Options" / "BarsPage_Options.lua").read_text()
        cls.widgets = (ROOT / "EllesmereUIOptions" / "EllesmereUI_Widgets_PageParts.lua").read_text()
        cls.movement = (ROOT / "EllesmereUIQoL" / "EllesmereUIQoL_MovementAlert.lua").read_text()

    def test_audio_text_fields_map_to_saved_keys(self):
        self.assertIn('soundField == "buffActiveSoundKey" then return "buffActiveTtsText"', self.focus)
        self.assertIn('soundField == "buffLostSoundKey" then return "buffLostTtsText"', self.focus)
        self.assertNotIn('field .. "TtsText"', self.focus + self.store + self.tracked)

    def test_runtime_and_saved_tiers_use_mapped_keys(self):
        self.assertIn('local textField = ns.AudioTextField(field)', self.focus)
        self.assertIn('ss and textField and ss[textField]', self.focus)
        self.assertIn('textField and rawget(own, textField)', self.store)
        self.assertIn('textField and tier[textField]', self.store)
        self.assertIn('textField and cfg[textField]', self.tracked)

    def test_mode_changes_preserve_existing_sound_and_custom_text_values(self):
        start = self.focus.index('function ns.SetAudioModeChoice(')
        end = self.focus.index('\nend', start) + len('\nend')
        setter = self.focus[start:end]
        tts_branch = setter[setter.index('if value == "tts" then'):setter.index('elseif value == "none" then')]
        none_start = setter.index('elseif value == "none" then')
        none_branch = setter[none_start:setter.index('\n    else', none_start)]
        self.assertIn('settings[ns.AudioModeField(soundField)] = "tts"', tts_branch)
        self.assertIn('settings[ns.AudioModeField(soundField)] = "none"', none_branch)
        self.assertNotIn('settings[soundField] =', tts_branch + none_branch)
        self.assertIn('settings[soundField] = value', setter)

    def test_editor_preview_uses_the_same_custom_text_and_default_fallback(self):
        self.assertIn('ns.PlayAudioCue("tts", ss[textField], spellID, event', self.options)

    def test_spell_picker_music_note_uses_event_audio_field_and_shared_tts_fallback(self):
        start = self.options.index('local function AddSoundPreview(si, item, textField, event)')
        end = self.options.index('-- "Audio on Buff Gain"', start)
        preview = self.options[start:end]
        self.assertIn('ns.PlayAudioCue("tts", ss[textField], spellID, event', preview)
        self.assertIn('if item.val == "tts" then', preview)
        self.assertIn('local paths = ns.FOCUSKICK_SOUND_PATHS', preview)
        self.assertIn('if path then PlaySoundFile(path, "Master") end', preview)
        self.assertIn('AddSoundPreview(si, item, "buffActiveTtsText", "gain")', self.options)
        self.assertIn('AddSoundPreview(si, item, "buffLostTtsText", "loss")', self.options)
        self.assertIn('local speech = EllesmereUI.ResolveCDMAudioText(text, spellID, event)', self.focus)
        self.assertIn('return EllesmereUI.DefaultCDMAudioText(spellID, event)', self.focus)
        self.assertNotIn('SetAudioModeChoice', preview)
        self.assertNotIn('RefreshCDMIconAppearance', preview)

    def test_music_note_tts_preview_is_independent_of_selected_mode(self):
        start = self.options.index('local function AddSoundPreview(si, item, textField, event)')
        end = self.options.index('-- "Audio on Buff Gain"', start)
        preview = self.options[start:end]
        self.assertIn('if item.val and item.val ~= "none" then', preview)
        click = preview[preview.index('play:SetScript("OnClick"'):]
        tts_start = click.index('if item.val == "tts" then')
        tts_branch = click[tts_start:click.index('local paths = ns.FOCUSKICK_SOUND_PATHS', tts_start)]
        self.assertIn('ns.PlayAudioCue("tts", ss[textField], spellID, event', tts_branch)
        self.assertNotIn('return end', tts_branch)
        self.assertNotIn('EffectiveAudioKey', tts_branch)

    def test_music_note_tts_preview_uses_inherited_spell_settings_and_text_fallback(self):
        start = self.options.index('local function AddSoundPreview(si, item, textField, event)')
        preview = self.options[start:self.options.index('-- "Audio on Buff Gain"', start)]
        effective = self.focus[self.focus.index('function ns.EffectiveAudioKey'):self.focus.index('function ns.AudioModeChoice')]
        self.assertIn('local mode = settings[ns.AudioModeField(soundField)]', effective)
        self.assertIn('local key = settings[soundField]', effective)
        self.assertIn('ns.ChainSettings(ss, (not isHostedBuff) and ns.GetBarTierSettings(sd, barKey) or nil)', self.options)
        self.assertIn('ns.PlayAudioCue("tts", ss[textField], spellID, event', preview)
        self.assertIn('local speech = EllesmereUI.ResolveCDMAudioText(text, spellID, event)', self.focus)
        self.assertIn('if type(text) == "string" and not text:match("^%s*$") then return text end', self.focus)
        self.assertIn('return EllesmereUI.DefaultCDMAudioText(spellID, event)', self.focus)

    def test_cooldown_and_utility_spell_picker_tts_previews_ignore_saved_mode(self):
        custom_start = self.options.index('local function AddCdrPreview(si, item)')
        custom_end = self.options.index('MakeSubnavRow("Audio Effect on CD Ready"', custom_start)
        custom_preview = self.options[custom_start:custom_end]
        tracked_start = self.options.index('local function AddCdrSoundPreview(si, item)')
        tracked_end = self.options.index('local cdReadySoundRow = MakeSubnavRow', tracked_start)
        tracked_preview = self.options[tracked_start:tracked_end]

        for preview in (custom_preview, tracked_preview):
            with self.subTest(context='custom-active' if preview is custom_preview else 'cooldown-or-utility'):
                self.assertIn('if item.val == "tts" then', preview)
                self.assertIn('ns.PlayAudioCue("tts",', preview)
                self.assertIn('spellID, "ready")', preview)
                self.assertNotIn('EffectiveAudioKey', preview)
                self.assertNotIn('SetAudioModeChoice', preview)

        # The shared dispatcher still resolves custom text or the spell/event
        # fallback, while runtime callers retain their separate mode gates.
        self.assertIn('local speech = EllesmereUI.ResolveCDMAudioText(text, spellID, event)', self.focus)
        self.assertIn('return EllesmereUI.DefaultCDMAudioText(spellID, event)', self.focus)
        self.assertIn('local soundKey = ns.EffectiveAudioKey(cas, "cdReadySoundKey")', self.fake_active)

    def test_none_mode_stays_silent_for_runtime_cooldown_and_buff_alerts(self):
        effective = self.focus[self.focus.index('function ns.EffectiveAudioKey'):self.focus.index('function ns.AudioModeChoice')]
        self.assertIn('if mode == "none" then return nil end', effective)
        self.assertIn('local key = ns.EffectiveAudioKey(ss2, "cdReadySoundKey")', self.watch)
        self.assertIn('if not key then', self.watch)
        self.assertIn('if key then', self.tracked[self.tracked.index('function ns.TBBPresetSoundEdge'):])
        self.assertIn('local key = ns.EffectiveAudioKey(ss, "buffActiveSoundKey")', self.custom_buffs)
        self.assertIn('local key = ns.EffectiveAudioKey(ss, "buffLostSoundKey")', self.custom_buffs)
        self.assertIn('if not key then return end', self.custom_buffs)

    def test_cdm_voice_and_volume_defaults_and_active_profile_resolution(self):
        defaults_start = self.cdm_main.index('local DEFAULTS = {')
        profile_start = self.cdm_main.index('profile = {', defaults_start)
        settings_start = profile_start + len('profile = {')
        settings_end = self.cdm_main.index('-- Style flags', settings_start)
        profile_defaults = self.cdm_main[settings_start:settings_end]
        self.assertIn('ttsVoiceID           = 0', profile_defaults)
        self.assertIn('ttsVolume            = 100', profile_defaults)

        start = self.focus.index('function ns.GetTTSSettings()')
        end = self.focus.index('\nend', start) + len('\nend')
        getter = self.focus[start:end]
        self.assertIn('ns.ECME and ns.ECME.db and ns.ECME.db.profile', getter)
        self.assertIn('profile.ttsVoiceID', getter)
        self.assertIn('profile.ttsVolume', getter)
        self.assertNotIn('EllesmereUIDB', getter)

    def test_all_cdm_tts_dispatch_uses_profile_voice_and_volume(self):
        start = self.focus.index('function ns.PlayAudioCue(')
        end = self.focus.index('\nend', start) + len('\nend')
        dispatcher = self.focus[start:end]
        self.assertIn('return ns.SpeakTTS(speech)', dispatcher)
        start = self.focus.index('function ns.SpeakTTS(')
        end = self.focus.index('\nend', start) + len('\nend')
        speaker = self.focus[start:end]
        self.assertIn('local voiceID, volume = ns.GetTTSSettings()', speaker)
        self.assertIn('EllesmereUI.SpeakText(text, voiceOverride or voiceID, volume)', speaker)
        self.assertIn('ns.PlayAudioCue(key, text, sid, "ready")', self.watch)
        self.assertIn('ns.PlayAudioCue(key, ss and ss.buffActiveTtsText, sid, "gain")', self.custom_buffs)
        self.assertIn('ns.PlayAudioCue(key, ss and ss.buffLostTtsText, sid, "loss")', self.custom_buffs)
        self.assertIn('ns.PlayAudioCue(soundKey, cas and cas.cdReadyTtsText, sid, "ready")', self.fake_active)

    def test_cdm_settings_ui_and_explicit_previews_use_profile_preferences(self):
        self.assertGreater(self.bars_page.index('W:SectionHeader(parent, "TEXT TO SPEECH"'),
                           self.bars_page.index('W:SectionHeader(parent, "ADDITIONAL BAR OFFSET"'))
        self.assertIn('profile.ttsVoiceID = value', self.bars_page)
        self.assertIn('profile.ttsVolume = value', self.bars_page)
        self.assertIn('min = 0, max = 100, step = 5', self.bars_page)
        self.assertIn('BuildTTSVoiceDropdownValues(function(voiceID)', self.bars_page)
        self.assertIn('ns.SpeakTTS("This is a voice preview", voiceID)', self.bars_page)

        self.assertIn('function EllesmereUI.ShowTTSTextPopup(title, initial, defaultText, onSave, onPreview)', self.widgets)
        self.assertIn('popup._onPreview(text ~= "" and text or popup._defaultText)', self.widgets)
        for source in (self.options, self.buff_page):
            self.assertIn('ns.PlayAudioCue("tts", text,', source)
        self.assertIn('ns.PlayAudioCue("tts", ss[textField], spellID, event)', self.options)
        self.assertIn('ns.PlayAudioCue("tts", cas.cdReadyTtsText, spellID, "ready")', self.options)
        self.assertIn('ns.PlayAudioCue("tts", ss.cdReadyTtsText, spellID, "ready")', self.options)

    def test_cdm_changes_leave_movement_alert_values_and_default_preview_intact(self):
        for field, default in (("maTtsVoiceID", "0"), ("maTtsVolume", "100"),
                               ("tsTtsVoiceID", "0"), ("tsTtsVolume", "100"),
                               ("gwTtsVoiceID", "0"), ("gwTtsVolume", "100")):
            self.assertRegex(self.movement, rf'{field}\s*=\s*{default}')
        self.assertIn('SpeakAlertText(msg, ma[prefix .. "TtsVoiceID"], ma[prefix .. "TtsVolume"])', self.movement)
        self.assertIn('EllesmereUI.SpeakText("This is a voice preview", key, 100)', self.widgets)

    def test_tracked_bar_editor_and_preview_use_canonical_text_key(self):
        self.assertIn('local function GetAudioTextFieldAndValue(soundField)', self.buff_page)
        self.assertIn('local textField = ns.AudioTextField(soundField)', self.buff_page)
        self.assertIn('if textField and cfg[textField] == nil and type(cfg[legacyField]) == "string" then', self.buff_page)
        self.assertIn('cfg[textField] = cfg[legacyField]', self.buff_page)
        self.assertIn('cfg[legacyField] = nil', self.buff_page)
        self.assertIn('ns.PlayAudioCue("tts", text, sid, event', self.buff_page)
        self.assertNotIn('field .. "TtsText"', self.buff_page)

    def test_cold_buff_activate_resolves_cd_scoped_record_and_inherited_tier(self):
        resolver = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookResolve.lua").read_text()
        self.assertIn('if not bk and isBuffViewerFrame and ns.GetBuffBarTierForSpell then', resolver)
        self.assertIn('tier = ns.GetBuffBarTierForSpell(sid2)', resolver)
        self.assertIn('ss = ns.ResolveSpellSettings and ns.ResolveSpellSettings(f, sid, nil, nil)', self.focus)
        self.assertIn('or f.viewerFrame == _G.BuffIconCooldownViewer', self.focus)
        self.assertIn('local settingsBarKey = bk or (isBuffViewerFrame and "buffs")', resolver)
        self.assertIn('frame.viewerFrame == _G.BuffIconCooldownViewer', resolver)
        self.assertIn('frame.viewerFrame == _G.BuffBarCooldownViewer', resolver)
        start = resolver.index("-- Per-cooldownID buff override:")
        end = resolver.index("-- Split-identity buffs", start)
        branch = resolver[start:end]
        self.assertIn('local cd = settings["c" .. cdID]', branch)
        self.assertIn('if cd then ChainSettings(cd, tier); return cd end', branch)
        self.assertLess(branch.index('local cd = settings["c" .. cdID]'), branch.index('if cd then ChainSettings(cd, tier); return cd end'))

    def test_decorated_and_cold_paths_share_buff_tier_source(self):
        resolver = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookResolve.lua").read_text()
        self.assertIn('ns.GetBarTierSettings(sd2, bk)', resolver)
        self.assertIn('ns.GetBuffBarTierForSpell(sid2)', resolver)
        self.assertIn('local tier = ns.GetBuffBarTierForProfile(prof, sid)', self.store)
        self.assertIn('ns.GetBuffBarTierForProfile(prof, sid)', self.store[self.store.index('function ns.FindBuffSoundKey'):])

    def test_explicit_none_and_sound_modes_override_inherited_tts(self):
        self.assertIn('if mode == "none" then return nil end', self.focus)
        self.assertIn('local key = settings[soundField]', self.focus)
        self.assertIn('return key', self.focus[self.focus.index('function ns.EffectiveAudioKey'):])
        self.assertIn('if not k and (mode ~= nil or configuredKey ~= nil) then', self.focus)

    def test_tier_without_custom_text_uses_default_for_both_buff_edges(self):
        self.assertIn('if type(text) == "string" and not text:match("^%s*$") then return text end', self.focus)
        self.assertIn('return EllesmereUI.DefaultCDMAudioText(spellID, event)', self.focus)
        self.assertIn('function ns.AudioTextField(soundField)', self.focus)
        self.assertIn('gainEdge and "gain" or "loss"', self.focus)

    def test_spell_picker_refreshes_buff_tts_editor_after_inherited_override_breakout(self):
        start = self.options.index('if canApply and AB.KeysBarApplied(applyKeys) and not AB.SpellHasOwn(applyKeys) then')
        end = self.options.index('end)\n\n                            if onItemCreated then', start)
        breakout = self.options[start:end]
        self.assertIn('doWrite()\n                                    -- Breaking away from a bar-applied value', breakout)
        self.assertIn('RefreshFlyoutSelection()\n                                    UpdateLabelColor()\n                                    return', breakout)
        self.assertIn('onRefresh = function()\n                                  local textRow = audioTextRows.buffActiveSoundKey', self.options)
        self.assertIn('onRefresh = function()\n                                  local textRow = audioTextRows.buffLostSoundKey', self.options)
        self.assertIn('if opts and opts.onRefresh then opts.onRefresh() end', self.options)

    def test_buff_audio_mode_transitions_recompute_tts_editor_enabled_state(self):
        refresh_start = self.options.index('local function RefreshAudioTextRow()')
        refresh_end = self.options.index('end\n                        RefreshAudioTextRow()', refresh_start)
        refresh = self.options[refresh_start:refresh_end]
        self.assertIn('ns.EffectiveAudioKey(ss, soundField) == "tts"', refresh)
        self.assertIn('row:EnableMouse(enabled)', refresh)
        self.assertIn('ns.SetAudioModeChoice(ss, "buffActiveSoundKey", v)', self.options)
        self.assertIn('ns.SetAudioModeChoice(ss, "buffLostSoundKey", v)', self.options)
        self.assertIn('if mode == "tts" then', self.focus)
        self.assertIn('if mode == "none" then return nil end', self.focus)
        self.assertIn('settings[ns.AudioModeField(soundField)] = "sound"', self.focus)

    def test_buff_bars_editor_refreshes_mode_on_selection_without_page_rebuild(self):
        set_start = self.buff_page.index('local function Set(v)')
        set_end = self.buff_page.index('local function ShowFlyout()', set_start)
        setter = self.buff_page[set_start:set_end]
        self.assertIn('ns.SetAudioModeChoice(cfg, field, v)', setter)
        self.assertIn('local enabled = v == "tts"', setter)
        self.assertIn('textRow:EnableMouse(enabled)', setter)
        self.assertIn('if sm._ttsField == field and textRow then', setter)

    def test_charge_ready_uses_only_never_secret_state_and_waits_for_full_recovery(self):
        watcher = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookIconWatch.lua").read_text()
        ready_start = watcher.index('local function CdReadyIsReady(')
        ready_end = watcher.index('\nend', ready_start) + len('\nend')
        ready = watcher[ready_start:ready_end]
        self.assertIn('if ci ~= nil and (ci.maxCharges or 0) > 1 then', ready)
        self.assertIn('return not ci.isActive', ready)
        self.assertNotIn('currentCharges', ready)
        self.assertIn('if CdReadyIsChargeSpell(livea) then\n            return', watcher)

    def test_ordinary_cooldown_ready_keeps_event_and_cooldown_detection(self):
        watcher = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookIconWatch.lua").read_text()
        self.assertIn('ef:RegisterEvent("SPELL_UPDATE_COOLDOWN")', watcher)
        self.assertIn('ef:RegisterEvent("SPELL_UPDATE_CHARGES")', watcher)
        self.assertIn('cd:HookScript("OnCooldownDone"', watcher)
        self.assertIn('hooksecurefunc(frame, "TriggerAvailableAlert"', watcher)

    def test_temporary_diagnostic_command_and_helpers_are_removed(self):
        events = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_Events.lua").read_text()
        self.assertNotIn('euittsdebug', events.lower())
        for source in (self.focus, self.options, self.buff_page, events):
            self.assertNotIn('DebugBuffTTS', source)
            self.assertNotIn('DebugCdReadyAudio', source)

    def test_audio_gates_recompute_from_legacy_and_tts_settings(self):
        start = self.store.index('function ns.RefreshAudioEnabledState()')
        end = self.store.index('\nend', start) + len('\nend')
        refresh = self.store[start:end]
        self.assertIn('local anyCDReady, anyBuffGain, anyBuffLoss = false, false, false', refresh)
        self.assertIn('ns.ForEachSavedSettingsBlock(function(ss)', refresh)
        self.assertIn('ns.EffectiveAudioKey(ss, "cdReadySoundKey")', refresh)
        self.assertIn('ns.EffectiveAudioKey(ss, "buffActiveSoundKey")', refresh)
        self.assertIn('ns.EffectiveAudioKey(ss, "buffLostSoundKey")', refresh)
        self.assertIn('ns.EffectiveAudioKey(settings, "cdReadySoundKey")', refresh)
        self.assertIn('if ns.TBBAnyBuffSound then anyTBBGain, anyTBBLoss = ns.TBBAnyBuffSound() end', refresh)
        self.assertIn('ns._cdmAnyCdReadySound = anyCDReady', refresh)
        self.assertIn('ns._cdmAnyBuffActiveSound = anyBuffGain or anyTBBGain', refresh)
        self.assertIn('ns._cdmAnyBuffLostSound = anyBuffLoss or anyTBBLoss', refresh)
        self.assertIn('ns._cdmAnyBuffSound = ns._cdmAnyBuffActiveSound or ns._cdmAnyBuffLostSound', refresh)
        self.assertIn('ns._tbbAnyBuffSound = anyTBB', refresh)
        self.assertNotIn('ns._cdmAnyCdReadySound = ns._cdmAnyCdReadySound or', refresh)
        effective = self.focus[self.focus.index('function ns.EffectiveAudioKey'):self.focus.index('function ns.AudioModeChoice')]
        self.assertIn('local key = settings[soundField]', effective)
        self.assertIn('if not key or key == "none" then return nil end', effective)

    def test_audio_mode_writes_refresh_aggregate_gates(self):
        self.assertGreaterEqual(self.options.count('ns.RefreshAudioEnabledState()'), 4)
        self.assertIn('ns.RefreshAudioEnabledState()', self.buff_page)
        self.assertIn('ns.RefreshAudioEnabledState()', self.options[self.options.index('AB.FlipSessionGates = function(t)'):])
        setter = self.focus[self.focus.index('function ns.SetAudioModeChoice('):]
        self.assertIn('settings[ns.AudioModeField(soundField)] = "tts"', setter)
        self.assertIn('settings[ns.AudioModeField(soundField)] = "none"', setter)

    def test_never_enabled_audio_has_no_registered_runtime_watcher(self):
        refresh = self.store[self.store.index('function ns.RefreshAudioEnabledState()'):]
        self.assertIn('local anyCDReady, anyBuffGain, anyBuffLoss = false, false, false', refresh)
        self.assertIn('ns._cdmAnyCdReadySound = anyCDReady', refresh)
        sync = self.watch[self.watch.index('local function SyncCdReadySoundEvents()'):]
        self.assertIn('local active = next(ns._cdReadySoundWatch) ~= nil', sync)
        self.assertIn('if active and not ef then', sync)
        watch = self.watch[self.watch.index('function ns.WatchCdReadySoundIfEnabled('):]
        self.assertLess(watch.index('if not ns._cdmAnyCdReadySound then'), watch.index('ResolveSpellSettings(frame'))

    def test_cd_ready_events_register_only_with_watchers_and_unregister_when_empty(self):
        start = self.watch.index('local function SyncCdReadySoundEvents()')
        end = self.watch.index('\nend', start) + len('\nend')
        sync = self.watch[start:end]
        self.assertIn('local active = next(ns._cdReadySoundWatch) ~= nil', sync)
        self.assertIn('ef:RegisterEvent("SPELL_UPDATE_COOLDOWN")', sync)
        self.assertIn('ef:RegisterEvent("SPELL_UPDATE_CHARGES")', sync)
        self.assertIn('ef:UnregisterEvent("SPELL_UPDATE_COOLDOWN")', sync)
        self.assertIn('ef:UnregisterEvent("SPELL_UPDATE_CHARGES")', sync)
        self.assertIn('elseif not active and ns._cdReadySoundEventsRegistered then', sync)
        refresh = self.watch[self.watch.index('function ns.RefreshCdReadyAudioWatchState()'):]
        self.assertIn('if not ns._cdmAnyCdReadySound then', refresh)
        self.assertIn('ns._cdReadySoundWatch[frame] = nil', refresh)
        self.assertIn('SyncCdReadySoundEvents()', refresh)

    def test_disabling_one_cooldown_alert_keeps_other_watchers_registered(self):
        sync = self.watch[self.watch.index('local function SyncCdReadySoundEvents()'):]
        self.assertIn('local active = next(ns._cdReadySoundWatch) ~= nil', sync)
        watcher = self.watch[self.watch.index('function ns.WatchCdReadySoundIfEnabled('):]
        branch = watcher[watcher.index('elseif ns._cdReadySoundWatch[frame] then'):]
        self.assertIn('ns._cdReadySoundWatch[frame] = nil', branch)
        self.assertIn('SyncCdReadySoundEvents()', branch)
        self.assertNotIn('ns._cdmAnyCdReadySound = false', watcher)

    def test_retained_runtime_hooks_return_before_resolution_when_disabled(self):
        record_start = self.focus.index('local function RecordBuffEdge(')
        record = self.focus[record_start:self.focus.index('\n    end', record_start)]
        self.assertIn('if gainEdge and not ns._cdmAnyBuffActiveSound then return end', record)
        self.assertIn('if not gainEdge and not ns._cdmAnyBuffLostSound then return end', record)
        self.assertLess(record.index('if gainEdge and not ns._cdmAnyBuffActiveSound then return end'), record.index('GetCanonicalSpellIDForFrame'))
        self.assertIn('if not ns._cdmAnyCdReadySound or ns._cdReadySoundWatch[f] ~= fd then return end', self.watch)
        self.assertIn('if not ns._cdmAnyCdReadySound or ns._cdReadySoundWatch[frame] ~= fd then return end', self.watch)
        self.assertIn('if not isBuffFamilyBar and ns.WatchCdReadySoundIfEnabled then', self.icons)

    def test_disabling_one_buff_edge_leaves_the_other_edge_active(self):
        refresh = self.store[self.store.index('function ns.RefreshAudioEnabledState()'):]
        self.assertIn('ns._cdmAnyBuffActiveSound = anyBuffGain or anyTBBGain', refresh)
        self.assertIn('ns._cdmAnyBuffLostSound = anyBuffLoss or anyTBBLoss', refresh)
        record = self.focus[self.focus.index('local function RecordBuffEdge('):]
        self.assertIn('if gainEdge and not ns._cdmAnyBuffActiveSound then return end', record)
        self.assertIn('if not gainEdge and not ns._cdmAnyBuffLostSound then return end', record)
        self.assertIn('if gainEdge then otherEnabled = ns._cdmAnyBuffLostSound', record)
        self.assertIn('else otherEnabled = ns._cdmAnyBuffActiveSound end', record)
        tbb = self.tracked[self.tracked.index('function ns.TBBAnyBuffSound()'):]
        self.assertIn('return gain, loss', tbb)
        self.assertIn('if c.enabled ~= false and c.trackType ~= "cooldown" then', tbb)
        custom = (ROOT / "EllesmereUICooldownManager" / "EUI_CDM_HookCustomBuffs.lua").read_text()
        self.assertIn('if not ns._cdmAnyBuffActiveSound then return end', custom)
        self.assertIn('if not ns._cdmAnyBuffLostSound then return end', custom)


if __name__ == "__main__":
    unittest.main()
