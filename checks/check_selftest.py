#!/usr/bin/env python3
"""Положительный и отрицательные контроли конечной проверки; только temp-файлы.

Данные: data/data.txt и src/hom_models.py в --root; оригиналы не изменяются.
Проверка: src/quick_fit.py создаёт temp JSON; checks/check.py принимает
корректный результат и отвергает испорченные V0, параметр и отпечаток.
Используется в: учебном опыте недели 2; не заменяет опыт пользователя с Goose.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    code_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=code_root)
    args = parser.parse_args()
    root = args.root.resolve()
    checker = code_root/"checks/check.py"
    with tempfile.TemporaryDirectory(prefix="hom_check_") as folder:
        folder = Path(folder)
        valid = folder/"valid.json"
        subprocess.run([sys.executable, "-B", str(code_root/"src/quick_fit.py"),
                        "--root", str(root), "--result", str(valid)], check=True)
        original = json.loads(valid.read_text(encoding="utf-8"))
        cases = [("valid", original, 0)]
        bad_v0 = copy.deepcopy(original)
        bad_v0["derived"]["V0"] += 0.02
        cases.append(("bad_V0", bad_v0, 1))
        bad_parameter = copy.deepcopy(original)
        bad_parameter["parameters"]["V"] += 0.02
        cases.append(("bad_parameter", bad_parameter, 1))
        bad_digest = copy.deepcopy(original)
        bad_digest["data"]["sha256_numeric"] = "0"*64
        cases.append(("bad_digest", bad_digest, 1))
        for name, payload, expected in cases:
            path = folder/f"{name}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            run = subprocess.run([sys.executable, "-B", str(checker), "--root", str(root),
                                  "--result", str(path)], text=True, capture_output=True)
            print(f"{name}: exit={run.returncode}; {(run.stdout+run.stderr).strip()}")
            if run.returncode != expected:
                raise RuntimeError(f"Контроль {name}: ожидался exit={expected}")
        # Числовой отпечаток не зависит от Windows/Unix окончаний строк.
        crlf = folder/"data_crlf.txt"
        text = (root/"data/data.txt").read_text(encoding="utf-8")
        crlf.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        run = subprocess.run([sys.executable, "-B", str(checker), "--root", str(root),
                              "--data", str(crlf), "--result", str(valid)], text=True, capture_output=True)
        print(f"CRLF: exit={run.returncode}; {(run.stdout+run.stderr).strip()}")
        if run.returncode != 0:
            raise RuntimeError("CRLF должен сохранять числовой отпечаток")
    print("SELFTEST PASS: valid + CRLF accepted; 3 corruptions rejected; original results untouched.")


if __name__ == "__main__":
    main()
