import stanza

try:
    stanza.download("uk", download_method=stanza.DownloadMethod.REUSE_RESOURCES)
except:
    pass
