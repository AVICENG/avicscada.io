#!/usr/bin/env python3
"""AVIC License Generator — publisher-side tool. Keep the private key offline."""
from __future__ import annotations
import argparse, base64, json, uuid
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

FORMAT = "avic-license-v1"
def canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
def load_private(path):
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey): raise ValueError("Ожидается закрытый ключ Ed25519")
    return key
def issue(host_id, customer, points, private_key_path, output, features=(), expires_at=None, key_id="avic-ed25519-1"):
    host_id, customer = host_id.strip(), customer.strip()
    if not host_id: raise ValueError("Host ID обязателен")
    if not customer: raise ValueError("Заказчик обязателен")
    if int(points) < 0: raise ValueError("Лимит точек не может быть отрицательным")
    payload = {"format": FORMAT, "license_id": str(uuid.uuid4()), "host_id": host_id,
      "customer": customer, "issued_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
      "point_limit": int(points), "features": sorted(set(x.strip() for x in features if x.strip())),
      "expires_at": expires_at or None, "key_id": key_id}
    signature = load_private(private_key_path).sign(canonical(payload))
    result = dict(payload, signature=base64.b64encode(signature).decode("ascii"))
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def generate_keys(private_path, public_path, key_id="avic-ed25519-1"):
    private = Ed25519PrivateKey.generate()
    Path(private_path).parent.mkdir(parents=True, exist_ok=True)
    Path(public_path).parent.mkdir(parents=True, exist_ok=True)
    Path(private_path).write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    Path(public_path).write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    try: Path(private_path).chmod(0o600)
    except OSError: pass

def gui():
    root=tk.Tk(); root.title("AVIC License Generator"); root.geometry("620x430"); root.minsize(560,390)
    frm=ttk.Frame(root,padding=18); frm.pack(fill="both",expand=True); frm.columnconfigure(1,weight=1)
    vars={k:tk.StringVar() for k in ("host","customer","points","key","output","features","expiry")}
    vars["points"].set("100"); vars["features"].set("modbus_tcp,bacnet_ip")
    def row(r,label,key,browse=None):
        ttk.Label(frm,text=label).grid(row=r,column=0,sticky="w",pady=6)
        ttk.Entry(frm,textvariable=vars[key]).grid(row=r,column=1,sticky="ew",padx=8,pady=6)
        if browse: ttk.Button(frm,text="Обзор…",command=browse).grid(row=r,column=2,pady=6)
    row(0,"Host ID установки","host"); row(1,"Заказчик","customer"); row(2,"Лимит точек","points")
    row(3,"Доп. функции (через запятую)","features"); row(4,"Срок действия UTC (необязательно)","expiry")
    row(5,"Закрытый ключ издателя","key",lambda:vars["key"].set(filedialog.askopenfilename(title="Выбрать закрытый ключ",filetypes=[("PEM key","*.pem"),("All files","*.*")])) )
    row(6,"Файл лицензии","output",lambda:vars["output"].set(filedialog.asksaveasfilename(defaultextension=".aviclic",filetypes=[("AVIC License","*.aviclic"),("JSON","*.json")])) )
    ttk.Label(frm,text="Одна лицензия = один Host ID = одна установка. Закрытый ключ не передавать заказчику.",wraplength=570).grid(row=7,column=0,columnspan=3,sticky="w",pady=(12,16))
    def create():
        try:
            exp=vars["expiry"].get().strip() or None
            if exp:
                from datetime import datetime
                dt=datetime.fromisoformat(exp.replace("Z","+00:00"))
                if dt.tzinfo is None: raise ValueError("Для срока укажите часовой пояс, например Z")
                exp=dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
            result=issue(vars["host"].get(),vars["customer"].get(),int(vars["points"].get()),vars["key"].get(),vars["output"].get(),vars["features"].get().split(","),exp)
            messagebox.showinfo("Лицензия создана",f"Лицензия {result['license_id']}\nHost ID: {result['host_id']}\nТочек: {result['point_limit']}\nФайл: {vars['output'].get()}")
        except Exception as e: messagebox.showerror("Не удалось создать лицензию",str(e))
    ttk.Button(frm,text="ВЫПУСТИТЬ ЛИЦЕНЗИЮ",command=create).grid(row=8,column=0,columnspan=3,sticky="ew",pady=10)
    root.mainloop()

if __name__=="__main__":
    p=argparse.ArgumentParser(description="AVIC License Generator")
    sub=p.add_subparsers(dest="cmd")
    k=sub.add_parser("generate-keys",help="Создать пару ключей издателя"); k.add_argument("--private",required=True); k.add_argument("--public",required=True)
    i=sub.add_parser("issue",help="Выпустить подписанную лицензию"); i.add_argument("--host-id",required=True); i.add_argument("--customer",required=True); i.add_argument("--points",required=True,type=int); i.add_argument("--private-key",required=True); i.add_argument("--output",required=True); i.add_argument("--features",default=""); i.add_argument("--expires-at",default=None)
    a=p.parse_args()
    if a.cmd=="generate-keys": generate_keys(a.private,a.public); print("Ключи созданы. Закрытый ключ хранить только у издателя!")
    elif a.cmd=="issue":
        x=issue(a.host_id,a.customer,a.points,a.private_key,a.output,a.features.split(","),a.expires_at); print(f"Создана лицензия {x['license_id']} для Host ID {x['host_id']}: {x['point_limit']} точек")
    else: gui()
