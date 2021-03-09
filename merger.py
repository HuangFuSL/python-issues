import os
from pyissues import io as io_
from xml.parsers import expat

os.chdir("output")
issues = []
fails = []
for i in sorted(os.listdir(), key=lambda _: int(_.replace("issues-", "").replace(".xml.gz", ""))):
    print("Loading file %s" % (i, ))
    with open(i, "rb") as file:
        try:
            issues.extend(io_.xmlloadCompressed(file))
        except expat.ExpatError:
            print("Failed loading %s" % (i, ))
            fails.append(i)

with open("../issues.xml.gz", "wb") as file:
    io_.xmldumpCompressed(issues, file)
    file.flush()