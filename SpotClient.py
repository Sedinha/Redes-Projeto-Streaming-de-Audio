import socket
import pyaudio
import time
import threading
import json
# Codigo integralmente feito por Luiz Fernando Sperandio David

MENSAGEM_FIM_DADOS_MUSICA = "track_data_end"
TAMANHO_MENSAGEM_FIM_DADOS_MUSICA = len(MENSAGEM_FIM_DADOS_MUSICA)


def sendDados(socketCliente, msg: str):
    print(f'Mandando mensagem :"{msg}" para {socketCliente}')
    socketCliente.send(msg.encode())


def receberDados(socketCliente):
    msg = ""
    socketCliente.settimeout(3.0)
    try:
        receberBytes = socketCliente.recv(1024).decode()
        msg = receberBytes
        print(f"Mensagem {msg} de {socketCliente} recebida !")
        return msg
    except Exception as e:
        print(f'{e}')
    return ''


def baixarMusica(nome_msc, socketCliente):
    CHUNK = 44100 * 2 * 30  # CHUNK = RATE * CHANNELS * 30 SEGUNDOS
    bytesMusica = []
    cacheLocal[nome_msc.lower()] = bytesMusica
    feito = False
    print(f"RX streaming musica")
    bytes_arquivo = b""
    while not feito:
        data_musica = socketCliente.recv(CHUNK)
        bytesMusica.append(data_musica)
        bytes_arquivo += data_musica
        if bytes_arquivo[-TAMANHO_MENSAGEM_FIM_DADOS_MUSICA:] == MENSAGEM_FIM_DADOS_MUSICA.encode():
            feito = True
            continue
    print("A musica inteira foi enviada !")


def carregarMSC(socketCliente, nome_msc: str):
    sendDados(socketCliente, f"download {nome_msc}")
    resp = receberDados(socketCliente)
    if resp != "track_data_start":
        return
    t1 = threading.Thread(target=baixarMusica, args=(
        nome_msc, socketCliente), daemon=True)
    t1.start()


cacheLocal = {}
p = pyaudio.PyAudio()
listaCacheLocal = []


def tocarMusica(nome_msc: str):
    global replay
    global pause
    global play
    global loop
    bytesMusica = cacheLocal[nome_msc.lower()]
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True)
    print("Iniciando tocar conteudo")
    feito = False
    play = True
    i = 0
    bytes_arquivo = b""
    while not feito:
        try:
            if replay:
                replay = False
                i = 0
                continue
            if not play:
                break
            if pause:
                continue
            frame = bytesMusica[i]
            bytes_arquivo += frame
            if bytes_arquivo[-TAMANHO_MENSAGEM_FIM_DADOS_MUSICA:] == MENSAGEM_FIM_DADOS_MUSICA.encode():
                if loop:
                    bytes_arquivo = b""
                    i = 0
                    continue
                feito = True
                continue
            stream.write(frame)
            i += 1
        except Exception as err:
            print(f"Error: {err}")
    print("Finalizando tocar conteudo")
    play = False
    stream.stop_stream()
    stream.close()


def imprimirBiblioteca():
    linhas = [
        " _____________________________",
        "|                             |",
        "|         Biblioteca          |",
        "|_____________________________|"
    ]

    for linha in linhas:
        print(linha)


def getListaMsc(socketCliente):
    global listaCacheLocal
    sendDados(socketCliente, 'lista')
    listaMsc = receberDados(socketCliente)
    listaCacheLocal = listaMsc.lower().split('\n')


play = False
loop = False
replay = False
pause = False


socketCliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socketCliente.connect(("10.0.0.7", 3213))
nome_cliente = socket.gethostname()
ip_cliente = socket.gethostbyname(nome_cliente)


feito = False
musica = None

while not feito:
    print("___________________________________________________________\n|   1.Play        2. Resume     3. Restart    4. Stop     |\n|        5. Loop       6. Pause      7. Lista             |\n|         8. Change(msc)       9. List_Dipo               |\n|___________________10. Quit______________________________|")
    comando = input("Digite um comando: \n").lower()
    '''	
	print("___________________________________________________________")
    print("|   1.Play        2. Resume     3. Restart    4. Stop     |")
    print("|        5. Loop       6. Pause      7. Lista             |")
    print("|         8. Change(msc)       9. List_Dipo               |")"
    print("|___________________10. Quit______________________________|")
    '''
    if comando == "pause" or comando == "6":
        if play:
            print("Setting paused")
            pause = True
    elif comando == "resume" or comando == "2":
        if play:
            print("Setting resume")
            pause = False
    elif comando == "change" or comando == "8":
        if play:
            nova_musica = input("Digite o nome da nova musica: ").lower()
            musica = nova_musica
            play = False
    elif comando in ["restart", "replay"] or comando == "3":
        replay = True
    elif comando == "stop" or comando == "4":
        # TODO use a playing state for a specific thread
        if play:
            play = False
        if pause:
            pause = False
    elif comando == "loop" or comando == "5":
        loop = not loop
        print(f"Loop: {loop}")
    elif comando == "play" or comando == "1":
        if musica:
            if play:
                play = False
                time.sleep(3.0)
            if len(listaCacheLocal) == 0:
                getListaMsc(socketCliente)
            if musica not in listaCacheLocal:
                print(
                    f"Musica '{musica}' não encontrada. Please send 'lista' para ver a lista de musicas")
                continue
            if not musica in cacheLocal:
                print(f"Loading track '{musica}'")
                carregarMSC(socketCliente, musica)
            print(f"Tocando '{musica}'")
            sendDados(socketCliente, f"att_status {musica}")
            time.sleep(3.0)
            t = threading.Thread(target=tocarMusica,
                                 args=(musica,), daemon=True)
            t.start()
        else:
            print("Nenhuma musica selecionada. Por favor colocar o nome da musica.")
            musica = input("Coloque o nome da musica: ").lower()
            print("Por favor ")
    elif comando == "lista" or comando == "7":
        imprimirBiblioteca()
        getListaMsc(socketCliente)
        for i in listaCacheLocal:
            print(i)
    elif comando == "quit" or comando == "10":
        print(f"Sending {comando} to server")
        sendDados(socketCliente, comando)
        resp = receberDados(socketCliente)
        if not resp:
            continue
        elif resp.lower() == "goodbye":
            feito = True
            socketCliente.close()
            print('\nConexão Fechada !')
            break
        else:
            print(resp)
    elif comando == "lista_dispositivos" or comando == "9":
        sendDados(socketCliente, 'lista_dispositivos')
        devices = receberDados(socketCliente)
        print("\n")
        print("Dispositivos: \n")
        print(devices)
        indice_escolhido = input(
            '\nEscolha um indice para tocar a musica de um cliente ou (N) para voltar ao menu.\nEscolha um indice:  ').lower()
        if indice_escolhido == "n":
            continue
        elemento_escolhido = devices.split('\n')[int(indice_escolhido) - 1]
        elemento_dividido = elemento_escolhido.split("Musica: ")
        musica = elemento_dividido[1]
        if play:
            play = False
            print("Digite Play ou '1' no menu para tocar a musica.")
        else:
            print("Digite Play ou '1' no menu para tocar a musica.")
            # elif comando == "play(msc)_ip" or comando == "11":
    else:
        print("Invalid command.")

socketCliente.close()
p.terminate()
