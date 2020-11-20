from requests import get
from json import dumps
from time import sleep
import os


#Obtiene el ID a partir de un username, en caso de error retorna una cadena de texto vacía.
def get_id(username):
	resp = get("https://www.instagram.com/" + username + "/?__a=1")

	if resp.status_code == 200:
		return resp.json()["graphql"]["user"]["id"];

	return "";
	
def save_file(link, path, reintentos = 3, sleep_error = 10):
	reintentos_actuales = 0
	descargado = False
	
	while(not descargado and reintentos_actuales < reintentos):
		resp_media = get(link)

		if(resp_media.status_code == 200):
			img = open(path, "wb")
			img.write(resp_media.content)
			img.close()
			
			descargado = True
		else:
			reintentos_actuales += 1
			sleep(sleep_error)
			
		
	return descargado
	
def ig_request(hash_id, variables, resolver, resolver_args = {}, cookies = {}, sleep_requests = 5, sleep_error = 10, reintentos = 3):
	has_next_page = True
	reintentos_actuales = 0
	
	params = {
		"query_hash": hash_id,
		"variables": dumps(variables)
	}
	
	while(has_next_page and reintentos_actuales < reintentos):
		resp = get("https://www.instagram.com/graphql/query/", params = params, cookies = cookies)
		
		if(resp.status_code == 200):
			reintentos_actuales = 0

			try:
				has_next_page = resolver(variables, resp.json(), resolver_args);
				
				if(has_next_page):
					params["variables"] = dumps(variables)
					sleep(sleep_requests)
					
			except Exception as err:
				print("Se prudujo un error en el resolver:", err)
				reintentos_actuales = reintentos #si se produjo un error salimos del bucle inesperadamente
			
		else:
			reintentos_actuales += 1
			
			print("Se ha producido un error en la petición, estamos realizando el reintento %d de %d reintentos posibles." % (reintentos_actuales, reintentos))
			
			sleep(sleep_error)
			
	
	return reintentos_actuales < reintentos


nro_media = 0 #variable global para sumar la cantidad de media descargada hasta el momento
def resolver_media(variables, data_resp, extra_args):
	global nro_media
	
	folder_name = extra_args["folder_name"]
	data_resp = data_resp["data"]["user"]["edge_owner_to_timeline_media"]
	
	#iteramos sobre los elementos multimedia y los guardamos
	for node in data_resp["edges"]:
		node = node["node"]
		
		if(node["__typename"] == "GraphSidecar"): #es un sidecar
			nro_img = 0
			for img in node["edge_sidecar_to_children"]["edges"]:
				is_save = save_file(img["node"]["display_url"], os.path.join(folder_name, str(nro_media) + "_" + str(nro_img) + ".jpg"))
				
				if(not is_save):
					raise Exception("Error al guardar el elemendo %d (de un Sidecar la imagen %d)." % (nro_media, nro_img))
					
				nro_img += 1
		else:
			ext = ".jpg"
			link = "display_url"
			
			if(node["__typename"] == "GraphVideo"):
				ext = ".mp4"
				link = "video_url"
				
			is_save = save_file(node[link], os.path.join(folder_name, str(nro_media) + ext))
			
			if(not is_save):
				raise Exception("Error al guardar el elemendo %d." % (nro_media))
		
		nro_media += 1
		print("(%d/%s)" % (nro_media, data_resp["count"]))

	if(data_resp["page_info"]["has_next_page"]):
		variables["after"] = data_resp["page_info"]["end_cursor"]
		return True
		
	return False
	
def get_all_media(id, folder_name):	
	variables = {
		"id": id,
		"first": 50
	}
	
	extra = {
		"folder_name": folder_name
	}
	
	return ig_request("003056d32c2554def87228bc3fd9668a", variables, resolver_media, resolver_args = extra)
		

def parse_args():
	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username', type=str, required=True, help="Target username.")
	
	return parser.parse_args()

args = parse_args()

if(not os.path.exists(os.path.join(os.getcwd(), args.username))):
	os.mkdir(args.username)

	id = get_id(args.username)
	if(id != ""):
		if(not get_all_media(id, args.username)):
			print("Se ha producido un error al obtener el contenido multimedia del usuario %s." % (args.username))
else:
	print("Por favor, elimine la carpeta %s que se encuentra en su directorio actual." % (args.username))