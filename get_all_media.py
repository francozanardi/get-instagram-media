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
	
def save_file(link, path, reintentos, sleep_error):
	reintentos_actuales = 0
	finalizado = False
	
	while(not finalizado and reintentos_actuales < reintentos):
		resp_media = get(link)

		if(resp_media.status_code == 200):
			img = open(path, "wb")
			img.write(resp_media.content)
			img.close()
			
			finalizado = True
		else:
			reintentos_actuales += 1
			sleep(sleep_error)
			
		
	return reintentos_actuales < reintentos

#A partir del ID del usuario 'id' obtenemos su contenido multimedia y lo guardamos en la carpeta 'folder_name'.
def get_all_media(id, folder_name, sleep_requests = 5, sleep_error = 10, reintentos = 3):
	has_next_page = True
	after = None
	reintentos_actuales = 0
	nro_media = 0
	
	variables = {
		"id": id,
		"first": 50,
		"after": after
	}
	
	params = {
		"query_hash": "003056d32c2554def87228bc3fd9668a",
		"variables": dumps(variables)
	}
	
	while(has_next_page and reintentos_actuales < reintentos):
		resp = get("https://www.instagram.com/graphql/query/", params = params)
		
		if(resp.status_code == 200):
			reintentos_actuales = 0
			data_resp = resp.json()["data"]["user"]["edge_owner_to_timeline_media"]
			
			#iteramos sobre los elementos multimedia y los guardamos
			for node in data_resp["edges"]:
				if(node["node"]["__typename"] == "GraphSidecar"): #es un sidecar
					nro_img = 0
					for img in node["node"]["edge_sidecar_to_children"]["edges"]:
						is_save = save_file(img["node"]["display_url"], os.path.join(folder_name, str(nro_media) + "_" + str(nro_img) + ".jpg"), reintentos, sleep_error)
						
						if(not is_save):
							reintentos_actuales = reintentos
							break
							
						nro_img += 1
				else:
					ext = ".jpg"
					link = "display_url"
					
					if(node["node"]["__typename"] == "GraphVideo"):
						ext = ".mp4"
						link = "video_url"
						
					is_save = save_file(node["node"][link], os.path.join(folder_name, str(nro_media) + ext), reintentos, sleep_error)
					
					if(not is_save):
						reintentos_actuales = reintentos
						break
				
				nro_media += 1
				print("(%d/%s)" % (nro_media, data_resp["count"]))
				
			

			has_next_page = data_resp["page_info"]["has_next_page"]
			
			if(has_next_page):
				variables["after"] = data_resp["page_info"]["end_cursor"]
				params["variables"] = dumps(variables)
				
				sleep(sleep_requests)
			
		else:
			reintentos_actuales += 1
			
			print("Se ha producido un error en la petición, estamos realizando el reintento %d de %d reintentos posibles." % (reintentos_actuales, reintentos))
			
			sleep(sleep_error)
			
	
	return reintentos_actuales < reintentos
		
		

username = input("Username: ")

if(not os.path.exists(os.path.join(os.getcwd(), username))):
	os.mkdir(username)

	id = get_id(username)
	if(id != ""):
		if(not get_all_media(id, username)):
			print("Se ha producido un error al obtener el contenido multimedia del usuario %s." % (username))
else:
	print("Por favor, elimine la carpeta %s que se encuentra en su directorio actual." % (username))