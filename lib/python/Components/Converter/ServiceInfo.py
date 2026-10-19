from enigma import eAVControl, iServiceInformation, iPlayableService, eServiceReference
from Components.Element import cached
from Components.Converter.Converter import Converter
from Components.config import config
from Components.Converter.Poll import Poll
from Components.Converter.VAudioInfo import StdAudioDesc
from Tools.Transponder import ConvertToHumanReadable
from Tools.DAB import dabMetadata

WIDESCREEN = [1, 3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10]


class ServiceInfo(Poll, Converter):
	HAS_TELETEXT = 1
	IS_MULTICHANNEL = 2
	AUDIO_STEREO = 3
	IS_CRYPTED = 4
	IS_WIDESCREEN = 5
	IS_NOT_WIDESCREEN = 6
	SUBSERVICES_AVAILABLE = 7
	XRES = 8
	YRES = 9
	APID = 10
	VPID = 11
	PCRPID = 12
	PMTPID = 13
	TXTPID = 14
	TSID = 15
	ONID = 16
	SID = 17
	FRAMERATE = 18
	TRANSFERBPS = 19
	HAS_HBBTV = 20
	AUDIOTRACKS_AVAILABLE = 21
	SUBTITLES_AVAILABLE = 22
	EDITMODE = 23
	IS_STREAM = 24
	IS_SD = 25
	IS_HD = 26
	IS_1080 = 27
	IS_720 = 28
	IS_576 = 29
	IS_480 = 30
	IS_4K = 31
	IS_SDR = 32
	IS_HDR = 33
	IS_HDR10 = 34
	IS_HLG = 35
	IS_HDHDR = 36
	FREQ_INFO = 37
	PROGRESSIVE = 38
	VIDEO_INFO = 39
	IS_SOFTCSA = 40
	IS_DAB = 41
	IS_DVBI = 42
	DAB_LANGUAGE = 43
	DAB_PROTECTION = 44
	DAB_METADATA = 45
	DAB_QUALITY = 46
	DAB_ENSEMBLE_ID = 47
	DAB_TECHNICAL = 48
	DAB_TEXT_FIELDS = {
		"DABArtist": iServiceInformation.sTagArtist,
		"DABBitrate": iServiceInformation.sTagBitrate,
		"DABChannel": iServiceInformation.sDABChannel,
		"DABCodec": iServiceInformation.sTagCodec,
		"DABDynamicLabel": iServiceInformation.sDABDynamicLabel,
		"DABEnsemble": iServiceInformation.sDABEnsembleLabel,
		"DABGenre": iServiceInformation.sTagGenre,
		"DABReceiver": iServiceInformation.sDABReceiverName,
		"DABTitle": iServiceInformation.sTagTitle
	}
	DAB_QUALITY_FIELDS = {
		"DABFICQuality": iServiceInformation.sDABFICQuality,
		"DABMSCQuality": iServiceInformation.sDABMSCQuality
	}

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		tokens = {
			"HasTelext": (self.HAS_TELETEXT, (iPlayableService.evUpdatedInfo,)),
			"IsMultichannel": (self.IS_MULTICHANNEL, (iPlayableService.evUpdatedInfo,)),
			"IsStereo": (self.AUDIO_STEREO, (iPlayableService.evUpdatedInfo,)),
			"IsCrypted": (self.IS_CRYPTED, (iPlayableService.evUpdatedInfo,)),
			"IsDAB": (self.IS_DAB, (iPlayableService.evStart, iPlayableService.evUpdatedInfo)),
			"DABEnsembleId": (self.DAB_ENSEMBLE_ID, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo)),
			"DABLanguage": (self.DAB_LANGUAGE, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo)),
			"DABProtection": (self.DAB_PROTECTION, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo)),
			"DABTechnical": (self.DAB_TECHNICAL, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo)),
			"IsDVBI": (self.IS_DVBI, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo)),
			"IsSoftCSA": (self.IS_SOFTCSA, (iPlayableService.evUpdatedInfo,)),
			"IsWidescreen": (self.IS_WIDESCREEN, (iPlayableService.evVideoSizeChanged,)),
			"IsNotWidescreen": (self.IS_NOT_WIDESCREEN, (iPlayableService.evVideoSizeChanged,)),
			"SubservicesAvailable": (self.SUBSERVICES_AVAILABLE, (iPlayableService.evUpdatedEventInfo,)),
			"VideoWidth": (self.XRES, (iPlayableService.evVideoSizeChanged,)),
			"VideoHeight": (self.YRES, (iPlayableService.evVideoSizeChanged,)),
			"AudioPid": (self.APID, (iPlayableService.evUpdatedInfo,)),
			"VideoPid": (self.VPID, (iPlayableService.evUpdatedInfo,)),
			"PcrPid": (self.PCRPID, (iPlayableService.evUpdatedInfo,)),
			"PmtPid": (self.PMTPID, (iPlayableService.evUpdatedInfo,)),
			"TxtPid": (self.TXTPID, (iPlayableService.evUpdatedInfo,)),
			"TsId": (self.TSID, (iPlayableService.evUpdatedInfo,)),
			"OnId": (self.ONID, (iPlayableService.evUpdatedInfo,)),
			"Sid": (self.SID, (iPlayableService.evUpdatedInfo,)),
			"Framerate": (self.FRAMERATE, (iPlayableService.evVideoSizeChanged, iPlayableService.evUpdatedInfo,)),
			"Progressive": (self.PROGRESSIVE, (iPlayableService.evVideoProgressiveChanged, iPlayableService.evUpdatedInfo,)),
			"VideoInfo": (self.VIDEO_INFO, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoFramerateChanged, iPlayableService.evVideoProgressiveChanged, iPlayableService.evVideoGammaChanged, iPlayableService.evUpdatedInfo,)),
			"TransferBPS": (self.TRANSFERBPS, (iPlayableService.evUpdatedInfo,)),
			"HasHBBTV": (self.HAS_HBBTV, (iPlayableService.evUpdatedInfo, iPlayableService.evHBBTVInfo,)),
			"AudioTracksAvailable": (self.AUDIOTRACKS_AVAILABLE, (iPlayableService.evUpdatedInfo,)),
			"SubtitlesAvailable": (self.SUBTITLES_AVAILABLE, (iPlayableService.evUpdatedInfo,)),
			"Freq_Info": (self.FREQ_INFO, (iPlayableService.evUpdatedInfo,)),
			"Editmode": (self.EDITMODE, (iPlayableService.evUpdatedInfo,)),
			"IsStream": (self.IS_STREAM, (iPlayableService.evUpdatedInfo,)),
			"IsSD": (self.IS_SD, (iPlayableService.evVideoSizeChanged,)),
			"IsHD": (self.IS_HD, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"Is1080": (self.IS_1080, (iPlayableService.evVideoSizeChanged,)),
			"Is720": (self.IS_720, (iPlayableService.evVideoSizeChanged,)),
			"Is576": (self.IS_576, (iPlayableService.evVideoSizeChanged,)),
			"Is480": (self.IS_480, (iPlayableService.evVideoSizeChanged,)),
			"Is4K": (self.IS_4K, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"IsSDR": (self.IS_SDR, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"IsHDR": (self.IS_HDR, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"IsHDR10": (self.IS_HDR10, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"IsHLG": (self.IS_HLG, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
			"IsHDHDR": (self.IS_HDHDR, (iPlayableService.evVideoSizeChanged, iPlayableService.evVideoGammaChanged,)),
		}
		# DAB
		tokens.update(dict.fromkeys(self.DAB_TEXT_FIELDS, (self.DAB_METADATA, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo))))
		tokens.update(dict.fromkeys(self.DAB_QUALITY_FIELDS, (self.DAB_QUALITY, (iPlayableService.evStart, iPlayableService.evEnd, iPlayableService.evUpdatedInfo))))
		# -----------------------------------
		self.type, self.interesting_events = tokens.get(type)
		self._token = type
		self.interesting_events += (iPlayableService.evStart,)

	def _isHDMIIn(self, info):
		return eServiceReference(info.getInfoString(iServiceInformation.sServiceref)).type == eServiceReference.idServiceHDMIIn

	def getServiceInfoString(self, info, what, convert=lambda x: "%d" % x):
		if self._isHDMIIn(info):
			return "N/A"
		v = info.getInfo(what)
		if v == -1:
			return "N/A"
		if v == -2:
			return info.getInfoString(what)
		return convert(v)

	def getServiceInfoHexString(self, info, what, convert=lambda x: "%04x" % x):
		v = info.getInfo(what)
		if v == -1:
			return "N/A"
		if v == -2:
			return info.getInfoString(what)
		return convert(v)

	def _getVideoHeight(self, info):
		if self._isHDMIIn(info):
			return -1
		val = eAVControl.getInstance().getResolutionY(0)
		return val if val else info.getInfo(iServiceInformation.sVideoHeight)

	def _getVideoHeightStr(self, info, convert=lambda x: "%d" % x if x > 0 else "?"):
		if self._isHDMIIn(info):
			return "?"
		val = eAVControl.getInstance().getResolutionY(0)
		return convert(val) if val else self.getServiceInfoString(info, iServiceInformation.sVideoHeight, convert)

	def _getVideoWidth(self, info):
		if self._isHDMIIn(info):
			return -1
		val = eAVControl.getInstance().getResolutionX(0)
		return val if val else info.getInfo(iServiceInformation.sVideoWidth)

	def _getVideoWidthStr(self, info, convert=lambda x: "%d" % x if x > 0 else "?"):
		if self._isHDMIIn(info):
			return "?"
		val = eAVControl.getInstance().getResolutionX(0)
		return convert(val) if val else self.getServiceInfoString(info, iServiceInformation.sVideoWidth, convert)

	def _getFrameRate(self, info):
		if self._isHDMIIn(info):
			return -1
		val = eAVControl.getInstance().getFrameRate(0)
		return val if val else info.getInfo(iServiceInformation.sFrameRate)

	def _getFrameRateStr(self, info, convert=lambda x: "%d" % x if x > 0 else ""):
		if self._isHDMIIn(info):
			return ""
		val = eAVControl.getInstance().getFrameRate(0)
		return convert(val) if val else self.getServiceInfoString(info, iServiceInformation.sFrameRate, convert)

	def _getProgressive(self, info):
		if self._isHDMIIn(info):
			return 0
		return eAVControl.getInstance().getProgressive()

	def _getProgressiveStr(self, info):
		if self._isHDMIIn(info):
			return "i"
		return "p" if eAVControl.getInstance().getProgressive() else "i"

	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		if self.type == self.DAB_QUALITY:
			return self.value >= 0  # Availability, including a measured zero.
		if self.type in (self.DAB_LANGUAGE, self.DAB_PROTECTION, self.DAB_METADATA, self.DAB_ENSEMBLE_ID, self.DAB_TECHNICAL):
			return bool(self.text)
		if not info:
			return False
		if self.type == self.IS_DVBI:
			return bool(service and getattr(self.source, "isDVBI", False))
		video_height = self._getVideoHeight(info)
		video_width = self._getVideoWidth(info)
		video_aspect = eAVControl.getInstance().getAspect(0)
		if not video_height:
			video_height = int(info.getInfo(iServiceInformation.sVideoHeight))
		if not video_aspect:
			video_aspect = info.getInfo(iServiceInformation.sAspect)
		if self.type == self.HAS_TELETEXT:
			tpid = info.getInfo(iServiceInformation.sTXTPID)
			return tpid != -1
		elif self.type in (self.IS_MULTICHANNEL, self.AUDIO_STEREO):
			audio = service.audioTracks()
			if audio:
				n = audio.getNumberOfTracks()
				idx = 0
				while idx < n:
					i = audio.getTrackInfo(idx)
					description = StdAudioDesc(i.getDescription())
					if description and description.split()[0] in ("AC4", "AAC+", "AC3", "AC3+", "Dolby", "DTS", "DTS-HD", "HE-AAC", "IPCM", "LPCM", "WMA Pro"):
						if self.type == self.IS_MULTICHANNEL:
							return True
						elif self.type == self.AUDIO_STEREO:
							return False
					idx += 1
				if self.type == self.IS_MULTICHANNEL:
					return False
				elif self.type == self.AUDIO_STEREO:
					return True
			return False
		elif self.type == self.IS_CRYPTED:
			return info.getInfo(iServiceInformation.sIsCrypted) == 1 and info.getInfo(iServiceInformation.sIsSoftCSA) != 1
		elif self.type == self.IS_SOFTCSA:
			return info.getInfo(iServiceInformation.sIsSoftCSA) == 1
		elif self.type == self.IS_DAB:
			ref = info.getInfoString(iServiceInformation.sServiceref)
			return bool(ref and eServiceReference(ref).type == eServiceReference.idServiceDAB)
		elif self.type == self.IS_WIDESCREEN:
			return video_aspect in WIDESCREEN
		elif self.type == self.IS_NOT_WIDESCREEN:
			return video_aspect not in WIDESCREEN
		elif self.type == self.SUBSERVICES_AVAILABLE:
			from Screens.InfoBarGenerics import hasActiveSubservicesForCurrentChannel  # noqa: E402
			return hasActiveSubservicesForCurrentChannel(info.getInfoString(iServiceInformation.sServiceref)) if not config.misc.hotkey.green.value else False
		elif self.type == self.HAS_HBBTV:
			return info.getInfoString(iServiceInformation.sHBBTVUrl) != ""
		elif self.type == self.AUDIOTRACKS_AVAILABLE:
			audio = service.audioTracks()
			return audio and audio.getNumberOfTracks() > 1
		elif self.type == self.SUBTITLES_AVAILABLE:
			subtitle = service and service.subtitle()
			subtitlelist = subtitle and subtitle.getSubtitleList()
			return bool(subtitlelist and len(subtitlelist) > 0)
		elif self.type == self.EDITMODE:
			return hasattr(self.source, "editmode") and not not self.source.editmode
		elif self.type == self.IS_STREAM:
			return service.streamed() is not None
		elif self.type == self.IS_SD:
			return video_height < 720
		elif self.type == self.IS_HD:
			return info.getInfo(iServiceInformation.sGamma) <= 0 and video_width >= 721 and video_width < 2160
		elif self.type == self.IS_1080:
			return video_height > 1000 and video_height <= 1080
		elif self.type == self.IS_720:
			return video_height > 700 and video_height <= 720
		elif self.type == self.IS_576:
			return video_height > 500 and video_height <= 576
		elif self.type == self.IS_480:
			return video_height > 0 and video_height <= 480
		elif self.type == self.IS_4K:
			return info.getInfo(iServiceInformation.sGamma) <= 0 and video_width >= 2160 and video_width <= 3840
		elif self.type == self.IS_SDR:
			return info.getInfo(iServiceInformation.sGamma) == 0
		elif self.type == self.IS_HDR:
			return video_width > 2160 and video_width <= 3840 and info.getInfo(iServiceInformation.sGamma) == 1
		elif self.type == self.IS_HDR10:
			return video_width > 2160 and video_width <= 3840 and info.getInfo(iServiceInformation.sGamma) == 2
		elif self.type == self.IS_HLG:
			return video_width > 2160 and video_width <= 3840 and info.getInfo(iServiceInformation.sGamma) == 3
		elif self.type == self.IS_HDHDR:
			return video_width >= 721 and video_width < 2160 and info.getInfo(iServiceInformation.sGamma) > 0
		elif self.type == self.PROGRESSIVE:
			return bool(self._getProgressive(info))
		return False

	boolean = property(getBoolean)

	@cached
	def getText(self):
		result = ""
		service = self.source.service
		info = service and service.info()
		if not info:
			return result
		if self.type in (self.DAB_LANGUAGE, self.DAB_PROTECTION, self.DAB_METADATA, self.DAB_QUALITY, self.DAB_ENSEMBLE_ID, self.DAB_TECHNICAL):
			if info:
				serviceRef = info.getInfoString(iServiceInformation.sServiceref)
				if serviceRef and eServiceReference(serviceRef).type == eServiceReference.idServiceDAB:
					if self.type == self.DAB_LANGUAGE:
						result = dabMetadata.languageName(info.getInfoString(iServiceInformation.sTagLanguageCode))
					elif self.type == self.DAB_PROTECTION:
						result = info.getInfoString(iServiceInformation.sDABProtection)
					elif self.type == self.DAB_QUALITY:
						quality = self.value
						result = f"{quality}%" if quality >= 0 else ""
					elif self.type == self.DAB_ENSEMBLE_ID:
						ensembleId = info.getInfo(iServiceInformation.sDABEnsembleId)
						result = f"{ensembleId:04X}" if ensembleId > 0 else ""
					elif self.type == self.DAB_TECHNICAL:
						channel = info.getInfoString(iServiceInformation.sDABChannel)
						parts = [f"SDR {channel}" if channel else "DVB"]
						values = [info.getInfoString(self.DAB_TEXT_FIELDS[x]) for x in ("DABCodec", "DABBitrate")]
						parts.extend(x for x in values if x)
						protection = info.getInfoString(iServiceInformation.sDABProtection)
						if protection:
							parts.append(protection)
						for name, field in (("FIC", iServiceInformation.sDABFICQuality), ("MSC", iServiceInformation.sDABMSCQuality)):
							quality = info.getInfo(field)
							if 0 <= quality <= 100:
								parts.append(f"{name} {quality}%")
						result = " | ".join(parts)
					else:
						result = info.getInfoString(self.DAB_TEXT_FIELDS[self.argument])
			return result
		elif self.type == self.XRES:
			return self._getVideoWidthStr(info)
		elif self.type == self.YRES:
			return self._getVideoHeightStr(info)
		elif self.type == self.APID:
			return self.getServiceInfoString(info, iServiceInformation.sAudioPID)
		elif self.type == self.VPID:
			return self.getServiceInfoString(info, iServiceInformation.sVideoPID)
		elif self.type == self.PCRPID:
			return self.getServiceInfoString(info, iServiceInformation.sPCRPID)
		elif self.type == self.PMTPID:
			return self.getServiceInfoString(info, iServiceInformation.sPMTPID)
		elif self.type == self.TXTPID:
			return self.getServiceInfoString(info, iServiceInformation.sTXTPID)
		elif self.type == self.TSID:
			return self.getServiceInfoString(info, iServiceInformation.sTSID)
		elif self.type == self.ONID:
			return self.getServiceInfoString(info, iServiceInformation.sONID)
		elif self.type == self.SID:
			return self.getServiceInfoHexString(info, iServiceInformation.sSID)
		elif self.type == self.FRAMERATE:
			video_rate = eAVControl.getInstance().getFrameRate(0)
			if not video_rate:
				try:
					video_rate = int(self.getServiceInfoString(info, iServiceInformation.sFrameRate))
				except Exception:
					return "N/A fps"
			return video_rate, lambda x: "%d fps" % ((x + 500) / 1000)
		elif self.type == self.PROGRESSIVE:
			return self._getProgressiveStr(info)
		elif self.type == self.TRANSFERBPS:
			return self.getServiceInfoString(info, iServiceInformation.sTransferBPS, lambda x: "%d kB/s" % (x / 1024))
		elif self.type == self.HAS_HBBTV:
			return info.getInfoString(iServiceInformation.sHBBTVUrl)
		elif self.type == self.FREQ_INFO:
			feinfo = service.frontendInfo()
			if feinfo is None:
				return ""
			feraw = feinfo.getAll(False)
			if feraw is None:
				return ""
			fedata = ConvertToHumanReadable(feraw)
			if fedata is None:
				return ""
			frequency = fedata.get("frequency")
			sr_txt = "Sr:"
			polarization = fedata.get("polarization_abbreviation")
			if polarization is None:
				polarization = ""
			symbolrate = str(int(fedata.get("symbol_rate", 0)))
			if symbolrate == "0":
				sr_txt = ""
				symbolrate = ""
			fec = fedata.get("fec_inner")
			if fec is None:
				fec = ""
			return "Freq: %s %s %s %s %s" % (frequency, polarization, sr_txt, symbolrate, fec)
		elif self.type == self.VIDEO_INFO:
			if self._isHDMIIn(info):
				return ""
			progressive = self._getProgressiveStr(info)
			fieldrate = self._getFrameRate(info)
			if fieldrate > 0:
				if progressive == 'i':
					fieldrate *= 2
				fieldrate = "%dHz" % ((fieldrate + 500) / 1000,)
			else:
				fieldrate = ""
			return "%sx%s%s %s" % (self._getVideoWidthStr(info), self._getVideoHeightStr(info), progressive, fieldrate)
		return ""

	text = property(getText)

	@cached
	def getValue(self):
		result = -1
		service = self.source.service
		info = service and service.info()
		if self.type == self.DAB_QUALITY:
			if info:
				serviceRef = info.getInfoString(iServiceInformation.sServiceref)
				if serviceRef and eServiceReference(serviceRef).type == eServiceReference.idServiceDAB:
					quality = info.getInfo(self.DAB_QUALITY_FIELDS[self.argument])
					if 0 <= quality <= 100:
						result = quality
			return result
		if not info:
			return -1
		if self.type == self.XRES:
			video_width = eAVControl.getInstance().getResolutionX(0)
			if not video_width:
				video_width = info.getInfo(iServiceInformation.sVideoWidth)
			return str(video_width)
		elif self.type == self.YRES:
			video_height = eAVControl.getInstance().getResolutionY(0)
			if not video_height:
				video_height = info.getInfo(iServiceInformation.sVideoHeight)
			return str(video_height)
		elif self.type == self.FRAMERATE:
			video_rate = eAVControl.getInstance().getFrameRate(0)
			if not video_rate:
				video_rate = info.getInfo(iServiceInformation.sFrameRate)
			return str(video_rate)
		return -1

	value = property(getValue)
	range = property(lambda self: 100 if self.token == self.DAB_QUALITY else None)

	def changed(self, what):
		if what[0] != self.CHANGED_SPECIFIC or what[1] in self.interesting_events:
			if len(what) > 1 and what[1] == iPlayableService.evStart:
				service = self.source.service
				info = service and service.info()
				if info and not self._isHDMIIn(info):
					return
			Converter.changed(self, what)
