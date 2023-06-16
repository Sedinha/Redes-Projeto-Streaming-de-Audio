import socket
import wave
import os
from threading import Thread
# Codigo integralmente feito por Luiz Fernando Sperandio David


def sendDados(socketCliente: socket, msg: bytes):
    print(f"Mandando a mensagem : {msg.decode()} pra {socketCliente}")
    socketCliente.send(msg)


def sendListaMusicas(socketCliente):
    pasta = os.listdir("./Biblioteca")
    musicas = []
    for arquivo in pasta:
        if arquivo.endswith(".wav"):
            # Remove a extensão do nome da música
            nome_musica = os.path.splitext(arquivo)[0]
            musicas.append(nome_musica)
    teladeMusicas = ''
    for musica in musicas:
        teladeMusicas += musica + "\n"
    teladeMusicas
    sendDados(socketCliente, teladeMusicas.encode())


def sendListaDispositivos(socketCliente):
    print("Dispositivos:\n")
    print(dict_dispositivos_sockets)
    lista = []
    for n, dispositivo in enumerate(dispositivos_conectados, 1):
        if len(dispositivo) == 2:
            enderecoCliente, enderecoCliente2 = dispositivo
            status = "None"
        else:
            enderecoCliente, enderecoCliente2, status = dispositivo
        listas = f'{n}-{enderecoCliente} ; {enderecoCliente2} Musica: {status}'
        lista.append(listas)
    lista_str = '\n'.join(lista)
    sendDados(socketCliente, lista_str.encode())


def checkExisteMusica(mscEscolhida):
    musicas = os.listdir("./Biblioteca")
    print(f'lista das musicas {musicas}')
    for (musica) in (musicas):
        # percorre a /Biblioteca para achar a musica escolhida pelo cliente
        nome_musica, extensao = os.path.splitext(musica)
        if mscEscolhida.lower() == nome_musica.lower():  # mscEscolhidaa padronizada
            print("song found")
            mscEscolhida = musica  # armazena novamente a mscEscolhida
            return True, mscEscolhida
    return False, mscEscolhida


def baixarMusicaCliente(mscEscolhida, socketCliente):
    mscEscolhida = "./Biblioteca/" + mscEscolhida
    wf = wave.open(mscEscolhida, 'rb')

    chunk = 44100 * 2 * 30

    print(f"chunk = {chunk}")
    # informa que onde começa o download
    sendDados(socketCliente, b"track_data_start")
    dataMsc = 1
    while dataMsc:
        # Qntde de data (30 segundos) sendo lidas e enviadas
        dataMsc = wf.readframes(chunk)
        print(f"Mandando 30 segundos de musica da musica: {mscEscolhida}")
        socketCliente.send(dataMsc)
    sendDados(socketCliente, b"track_data_end")
    print(f'A musica {mscEscolhida} foi enviada')


def clienttread(socketCliente, enderecoCliente):
    print(f"<{enderecoCliente} conectado>")
    feito = False
    while not feito:
        try:
            data = (socketCliente.recv(1024).decode())
            dataDownload = data.split(" ")
            if not data:
                raise (Exception)
            print(f"from connected {enderecoCliente} : {data}")
            if data == "lista" or data == "7":
                sendListaMusicas(socketCliente)
            elif dataDownload[0] == "download":
                exists, name = checkExisteMusica(dataDownload[1])
                if not exists:
                    sendDados(
                        socketCliente, f"Musica '{name}' não encontrada. Por favor envie 'lista' para ver a lista de musicas".encode())
                    continue
                try:
                    baixarMusicaCliente(name, socketCliente)
                except ConnectionResetError:
                    print(f"Connection was reset {enderecoCliente}")
                    feito = True
                    socketCliente.close()
                    continue
                except TimeoutError:
                    print(
                        f"Timeout Error, clossing connection to {enderecoCliente}")
                    feito = True
                    socketCliente.close()
                    continue
            elif data == "9" or data == "quit":
                feito = True
                sendDados(socketCliente, f"goodbye".encode())
                socketCliente.close()
                for dispositivo in dispositivos_conectados:
                    if len(dispositivo) == 3:
                        enderecoCliente1, enderecoClientes, musica = dispositivo
                    if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                        dispositivos_conectados.remove(dispositivo)
                    else:
                        enderecoCliente1, enderecoClientes = dispositivo
                        if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                            dispositivos_conectados.remove(dispositivo)
                continue

            elif data == "lista_dispositivos" or data == "10":
                sendListaDispositivos(socketCliente)

            elif dataDownload[0] == "att_status":
                print(f"Atualizando status para {dataDownload[1]}...")
                for dispositivo in dispositivos_conectados:
                    if len(dispositivo) == 3:
                        enderecoCliente1, enderecoClientes, musica = dispositivo
                        if enderecoCliente1 == enderecoCliente[0]:
                            dispositivo[2] = dataDownload[1]
                    else:
                        enderecoCliente1, enderecoClientes = dispositivo
                        if enderecoCliente1 == enderecoCliente[0]:
                            dispositivo.append(dataDownload[1])
                print(dispositivos_conectados)
            else:
                # 'elif data == "play(msc)_ip" or data == "11":
                sendDados(socketCliente, "Comando Inexistente.".encode())
        except ConnectionResetError:
            print(f"Coneção foi resetada {enderecoCliente}")
            feito = True
            socketCliente.close()
            for dispositivo in dispositivos_conectados:
                if len(dispositivo) == 3:
                    enderecoCliente1, enderecoClientes, musica = dispositivo
                    if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                        dispositivos_conectados.remove(dispositivo)
                else:
                    enderecoCliente1, enderecoClientes = dispositivo
                    if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                        dispositivos_conectados.remove(dispositivo)
            break
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            feito = True
            socketCliente.close()
            for dispositivo in dispositivos_conectados:
                if len(dispositivo) == 3:
                    enderecoCliente1, enderecoClientes, musica = dispositivo
                    if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                        dispositivos_conectados.remove(dispositivo)
                else:
                    enderecoCliente1, enderecoClientes = dispositivo
                    if enderecoCliente[0] == enderecoCliente1 and enderecoCliente[1] == enderecoClientes:
                        dispositivos_conectados.remove(dispositivo)
            break
    return


def obter_ip():
    try:
        # Cria um socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Conecta o socket a um servidor DNS
        sock.connect(("8.8.8.8", 80))

        # Obtém o endereço IP do socket
        ip = sock.getsockname()[0]

        # Fecha o socket
        sock.close()

        return ip
    except socket.error:
        return "Não foi possível obter o endereço IP"


ip = obter_ip()

endereco_servidor = ip
porta_servidor = 2635
max_conexoes = 5
socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_servidor.bind((endereco_servidor, porta_servidor))
socket_servidor.listen(max_conexoes)
print("Iniciando servidor. Aguardando novas conexões\n ... ")
print(ip)
dict_dispositivos_sockets = {}
dispositivos_conectados = []

while True:
    try:
        (socketCliente, enderecoCliente) = socket_servidor.accept()
        dict_dispositivos_sockets[enderecoCliente[0]] = socketCliente
        dispositivos_conectados.append(
            [enderecoCliente[0], enderecoCliente[1]])
    except socket.timeout:
        print(f"Servidor: Desligando thread de escuta")
        break
    tserver = Thread(target=clienttread, args=(
        socketCliente, enderecoCliente), daemon=True)
    tserver.start()
