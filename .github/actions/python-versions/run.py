import configparser
import os
import tomllib

tox_conf = configparser.ConfigParser(interpolation=None)
tox_conf.read("tox.ini", "utf-8")

with open("pyproject.toml", "rb") as f:
    pyproj = tomllib.load(f)

print(tox_conf)
print(tomllib)

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
    print("[]", file=f)
