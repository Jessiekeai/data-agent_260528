"""
  @Author:jiexi
  @Time:2026/9/29
  @Desc:
"""
from pathlib import Path

from attr import dataclass
from omegaconf import OmegaConf
import yaml


def parse_by_yaml():
    yaml_path = Path(__file__).resolve().parents[2] / "conf" / "test_config.yaml"

    with yaml_path.open("r", encoding="utf-8") as file:
        yaml_data = yaml.safe_load(file)
        print(yaml_data)
        print(type(yaml_data))


def parse_by_omega():
    yaml_path = Path(__file__).resolve().parents[2] / "conf" / "test_config.yaml"
    yaml_data = OmegaConf.load(yaml_path)
    print(yaml_data)
    print(type(yaml_data))
    print(yaml_data["name"], yaml_data.name)


@dataclass
class Person:
    name: str
    age: int
    height: float


def parse_by_omega2():
    yaml_path = Path(__file__).resolve().parents[2] / "conf" / "test_config.yaml"
    yaml_data = OmegaConf.load(yaml_path)
    person_config: Person = OmegaConf.to_object(OmegaConf.merge(Person, yaml_data))
    print(person_config)
    print(type(person_config))
    print(person_config.name)


if __name__ == "__main__":
    # parse_by_yaml()
    parse_by_omega()
    # parse_by_omega2()
