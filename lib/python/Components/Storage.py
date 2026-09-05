# Copyright (c) 2025 jbleyel

# This code may be used commercially. Attribution must be given to the original author.
# Licensed under GPLv2.


from os import listdir, rmdir
from os.path import ismount, join

from Tools.Directories import fileReadLines


def getProcMountsNew():
	lines = fileReadLines("/proc/mounts", default=[])
	result = []
	for line in [x for x in lines if x and x.startswith("/dev/")]:
		# Replace encoded space (\040) and newline (\012) characters with actual space and newline
		result.append([s.replace("\\040", " ").replace("\\012", "\n") for s in line.strip(" \n").split(" ")])
	return result


def cleanMediaDirs():
	mounts = getProcMountsNew()
	mounts = [x[1] for x in mounts if x[1].startswith("/media/")]
	for directory in listdir("/media"):
		if directory not in ("audiocd", "autofs", "hdd", "net"):
			mediaDirectory = join("/media/", directory)
			if mediaDirectory not in mounts and not ismount(mediaDirectory):
				print(f"[Storage] remove directory {mediaDirectory} because of unmount")
				try:
					rmdir(mediaDirectory)
				except Exception as err:
					print(f"[Storage] Error {err.errno}: Failed delete '{mediaDirectory}'!  ({err.strerror})")
