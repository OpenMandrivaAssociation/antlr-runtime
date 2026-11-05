Name:		antlr-runtime
Version:	3.5.3
Release:	1
Summary:	ANTLR 3 runtime
Group:		Development/Java
License:	BSD
URL:		https://www.antlr3.org/
Source0:	https://github.com/antlr/antlr3/archive/refs/tags/%{version}.tar.gz#/antlr3-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	stringtemplate
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
ANTLR 3 Java runtime. The tool and the other language targets are not
built. DOTTreeGenerator imports StringTemplate 3, so that jar stays a
dependency even though upstream marked it optional.

%prep
%autosetup -n antlr3-%{version}
cp -a tool/LICENSE.txt LICENSE.txt
rm -rf src
mv runtime/Java/src src
mv runtime/Java/pom.xml pom.xml
python - <<'PY'
import shutil
from pathlib import Path
keep = {"src", "pom.xml", "LICENSE.txt", "README.txt"}
for path in Path(".").iterdir():
    if path.name not in keep:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
PY
python - %{version} <<'PY'
import sys
import xml.etree.ElementTree as ET
version = sys.argv[1]
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def local(tag):
    return tag.split("}", 1)[-1]

tree = ET.parse("pom.xml")
root = tree.getroot()
for node in list(root):
    if local(node.tag) in {"parent", "build"}:
        root.remove(node)

def upsert(tag, text, after):
    for node in root:
        if local(node.tag) == tag:
            node.text = text
            return
    element = ET.Element(f"{{{NS}}}{tag}")
    element.text = text
    index = 0
    for i, node in enumerate(list(root)):
        if local(node.tag) == after:
            index = i + 1
    root.insert(index, element)

upsert("groupId", "org.antlr", "modelVersion")
upsert("version", version, "artifactId")
for dep in root.iter(f"{{{NS}}}dependency"):
    artifact = ""
    for node in dep:
        if local(node.tag) == "artifactId":
            artifact = (node.text or "").strip()
    if artifact == "junit":
        scope = None
        for node in dep:
            if local(node.tag) == "scope":
                scope = node
        if scope is None:
            scope = ET.SubElement(dep, f"{{{NS}}}scope")
        scope.text = "test"
tree.write("pom.xml", encoding="utf-8", xml_declaration=True)
PY

%files -f .mfiles
%doc LICENSE.txt README.txt
