# server/server.py
import socket
import threading
import json
import argparse
from tasks import GestionnaireTaches

HOST = "0.0.0.0"
PORT = 5000
ENC = "utf-8"

class ServeurTaches:
    def __init__(self, host=HOST, port=PORT, persistence_file="tasks.json"):
        self.host = host
        self.port = port
        self.gestionnaire = GestionnaireTaches(persistence_file=persistence_file)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._stop_event = threading.Event()

    def start(self):
        self._sock.bind((self.host, self.port))
        self._sock.listen(5)
        print(f"[Serveur] Écoute sur {self.host}:{self.port}")
        try:
            while not self._stop_event.is_set():
                client_sock, addr = self._sock.accept()
                print(f"[Serveur] Connexion de {addr}")
                t = threading.Thread(target=self.handle_client, args=(client_sock,addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            print("[Serveur] Arrêt demandé (KeyboardInterrupt)")
        finally:
            self.stop()

    def stop(self):
        self._stop_event.set()
        try:
            self._sock.close()
        except:
            pass
        print("[Serveur] Arrêté")

    def handle_client(self, client_sock: socket.socket, addr):
        # We'll use a file-like wrapper to read lines conveniently
        f = client_sock.makefile(mode="rw", encoding=ENC)
        try:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except json.JSONDecodeError:
                    resp = {"status":"error","message":"JSON invalide"}
                    f.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    f.flush()
                    continue

                action = req.get("action")
                if not action:
                    resp = {"status":"error","message":"champ 'action' requis"}
                    f.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    f.flush()
                    continue

                # dispatch
                if action == "add":
                    titre = req.get("titre","").strip()
                    description = req.get("description","")
                    auteur = req.get("auteur")
                    if not titre:
                        resp = {"status":"error","message":"titre requis"}
                    else:
                        t = self.gestionnaire.ajouter_tache(titre, description, auteur)
                        resp = {"status":"ok","tache": t.to_dict()}
                elif action == "list":
                    filtre_statut = req.get("statut")
                    filtre_auteur = req.get("auteur")
                    tasks = self.gestionnaire.lister_taches(filtre_statut, filtre_auteur)
                    resp = {"status":"ok","taches": tasks}
                elif action == "del":
                    tid = req.get("id")
                    try:
                        tid = int(tid)
                        ok = self.gestionnaire.supprimer_tache(tid)
                        resp = {"status":"ok" if ok else "error", "deleted": ok}
                    except:
                        resp = {"status":"error","message":"id invalide"}
                elif action == "status":
                    tid = req.get("id")
                    statut = req.get("statut")
                    if statut not in ("TODO","DOING","DONE"):
                        resp = {"status":"error","message":"statut invalide (TODO/DOING/DONE)"}
                    else:
                        try:
                            tid = int(tid)
                            ok = self.gestionnaire.changer_statut(tid, statut)
                            resp = {"status":"ok" if ok else "error", "changed": ok}
                        except:
                            resp = {"status":"error","message":"id invalide"}
                elif action == "save":
                    self.gestionnaire.sauvegarder_manuel()
                    resp = {"status":"ok","message":"sauvegardé"}
                elif action == "ping":
                    resp = {"status":"ok","message":"pong"}
                else:
                    resp = {"status":"error","message":"action inconnue"}
                f.write(json.dumps(resp, ensure_ascii=False) + "\n")
                f.flush()
        except Exception as e:
            print("[Serveur] Exception client", addr, e)
        finally:
            try:
                f.close()
            except:
                pass
            try:
                client_sock.close()
            except:
                pass
            print(f"[Serveur] Déconnexion de {addr}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--persist", default="tasks.json", help="fichier de persistence (ou '' pour désactiver)")
    args = parser.parse_args()
    persistence = args.persist if args.persist != "" else None
    srv = ServeurTaches(host=args.host, port=args.port, persistence_file=persistence)
    srv.start()
