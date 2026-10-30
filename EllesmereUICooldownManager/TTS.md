# Cooldown Manager TTS alerts

Cooldown Manager audio alerts can use an installed sound, native WoW text-to-speech, or no audio.

## Configure a spell alert

1. Open EllesmereUI options and select Cooldown Manager.
2. Open the spell's settings menu.
3. For a cooldown alert, set **Audio Effect on CD Ready**. For a tracked buff, set **Audio on Buff Gain** or **Audio on Buff Loss**.
4. Choose **Text to Speech**. Use the speaker icon to preview the default or saved message.
5. Choose **Edit TTS Message** to enter custom text, preview it, and save it. Leave the field empty to use the spell-based default.

Tracked buff bars have the same Sound, Text to Speech, and None choices in their audio menu, with a TTS message editor for each edge.

## Saved settings and inheritance

The existing sound-key field stores the selected sound or the reserved `__tts` value. A spell-level None stores `nil`, clearing its own choice and resuming inheritance from the bar. None applied to a bar writes `false` to block inherited audio. Selecting TTS replaces that level's sound choice; the previous sound is not retained.

Custom messages are saved per spell and event. Empty custom text uses the spell-based default. Voice and volume are shared by Cooldown Manager and saved in the active EUI profile; edits stay local to the message popup until Save. Cancel, Escape, or outside dismissal discards those drafts. Movement Alert keeps its independent voice and volume settings.

TTS requires the client to expose `C_VoiceChat.SpeakText` and have a usable speech voice configured in WoW and the operating system. If the API is unavailable, the TTS alert quietly does nothing. Sound alerts do not depend on TTS availability.

## Manual testing

Test a cooldown-ready alert, buff gain and loss, custom and default text, sound/None/TTS selection, Apply to Bar and Apply to Bar (All Specs), `/reload` persistence, profile switching, combat, rapid repeated events, popup Save/Cancel/Preview, and TTS with the client speech feature unavailable or disabled.
