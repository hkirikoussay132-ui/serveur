# client/client.py
import socket
import json
import argparse
import sys

ENC = "utf-8"

def send_request(sock, obj):
    s = json.dumps(obj, ensure_ascii=False) + "\n"
    sock.sendall(s.encode(ENC))
    # receive one line response
    resp = b""
    while True:
        c = sock.recv(4096)
        if not c:
            break
        resp += c
        if b"\n" in c:
            break
    if not resp:
        return None
    line = resp.decode(ENC).strip()
    try:
        return json.loads(line)
    except:
        return {"status":"error","message":"réponse non JSON", "raw": line}

def pretty_list(taches):
    if not taches:
        print("Aucune tâche.")
        return
    for t in taches:
        print(f"[{t['id']}] {t['titre']} ({t['statut']}) — auteur: {t.get('auteur')}")
        if t.get("description"):
            print("   ", t["description"])

def interactive(host, port, auteur=None):
    with socket.create_connection((host, port)) as sock:
        print(f"Connecté à {host}:{port}")
        while True:
            print("\nMenu:")
            print("1. Ajouter une tâche")
            print("2. Lister les tâches")
            print("3. Supprimer une tâche")
            print("4. Changer le statut")
            print("5. Sauvegarder (serveur)")
            print("6. Ping serveur")
            print("0. Quitter")
            choice = input("Choix: ").strip()
            if choice == "1":
                titre = input("Titre: ").strip()
                description = input("Description: ").strip()
                req = {"action":"add", "titre": titre, "description": description, "auteur": auteur}
                r = send_request(sock, req)
                print(r)
            elif choice == "2":
                statut = input("Filtrer par statut (TODO/DOING/DONE) ou Enter pour tous: ").strip().upper() or None
                if statut == "":
                    statut = None
                req = {"action":"list"}
                if statut:
                    req["statut"]=statut
                r = send_request(sock, req)
                if r and r.get("status") == "ok":
                    pretty_list(r.get("taches", []))
                else:
                    print(r)
            elif choice == "3":
                tid = input("ID à supprimer: ").strip()
                req = {"action":"del", "id": tid}
                r = send_request(sock, req)
                print(r)
            elif choice == "4":
                tid = input("ID: ").strip()
                statut = input("Nouveau statut (TODO/DOING/DONE): ").strip().upper()
                req = {"action":"status", "id": tid, "statut": statut}
                r = send_request(sock, req)
                print(r)
            elif choice == "5":
                req = {"action":"save"}
                r = send_request(sock, req)
                print(r)
            elif choice == "6":
                req = {"action":"ping"}
                r = send_request(sock, req)
                print(r)
            elif choice == "0":
                print("Au revoir.")
                return
            else:
                print("Choix invalide")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--auteur", help="nom de l'auteur pour les tâches", default=None)
    args = parser.parse_args()
    try:
        interactive(args.host, args.port, args.auteur)
    except ConnectionRefusedError:
        print("Impossible de se connecter au serveur. Vérifiez qu'il est lancé.")
    except KeyboardInterrupt:
        print("\nInterrompu.")
