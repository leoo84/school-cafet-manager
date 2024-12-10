#!/usr/bin/env python

import sys
directory = sys.argv[0][:-7]

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio # type: ignore
from datetime import datetime, timedelta
from functools import partial
import json
import sqlite3
import shutil
import openpyxl
from time import sleep

db = sqlite3.connect(directory + 'donnees.db')
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS ventes (date DATE, afternoon INTEGER, articles VARCHAR(2000))")
db.commit()
cursor.execute("CREATE TABLE IF NOT EXISTS approvisionnements (date DATE, articles VARCHAR(2000))")
db.commit()

def getSelledArticles(day, month, year, afternoon):
	cursor.execute('SELECT articles FROM ventes WHERE date = ? AND afternoon = ?', (f"{year}-{'0' * (2-len(str(month))) + str(month)}-{'0' * (2-len(str(day))) + str(day)}", afternoon))
	data = cursor.fetchall()
	if(data == []):
		return None
	else:
		return json.loads(data[0][0])

quantityLabels = {}
littlePriceLabel = Gtk.Label().set_text("0€")
bigPriceLabel = Gtk.Label().set_text("0€")

def sellArticle(day, month, year, afternoon, article, quantityLabel, widget):
	articles = getSelledArticles(day, month, year, afternoon)
	if(articles == None):
		articles = {}
		articles[article] = 1
		cursor.execute('INSERT INTO ventes (date, afternoon, articles) VALUES (?, ?, ?)', (f"{year}-{'0' * (2-len(str(month))) + str(month)}-{'0' * (2-len(str(day))) + str(day)}", afternoon, json.dumps(articles)))
		quantityLabel.set_text("1")
	else:
		try:
			articles[article] += 1
		except:
			articles[article] = 1
		cursor.execute('UPDATE ventes SET articles = ? WHERE date = ? AND afternoon = ?', (json.dumps(articles), f"{year}-{'0' * (2-len(str(month))) + str(month)}-{'0' * (2-len(str(day))) + str(day)}", afternoon))
		quantityLabel.set_text(str(articles[article]))
	db.commit()
	bigPriceLabel.set_text(f'{calc(day, month, year, afternoon)}€')
	littlePriceLabel.set_text(f'{calc(day, month, year, afternoon)}€')

def unsellArticle(day, month, year, afternoon, article, quantityLabel, widget):
	articles = getSelledArticles(day, month, year, afternoon)
	if(articles != None):
		try:
			if(articles[article] > 1):
				articles[article] -= 1
				quantityLabel.set_text(str(articles[article]))
			elif(articles[article] == 1):
				del articles[article]
				quantityLabel.set_text("0")
			cursor.execute('UPDATE ventes SET articles = ? WHERE date = ? AND afternoon = ?', (json.dumps(articles), f"{year}-{'0' * (2-len(str(month))) + str(month)}-{'0' * (2-len(str(day))) + str(day)}", afternoon))
			db.commit()
		except:
			pass
	bigPriceLabel.set_text(f'{calc(day, month, year, afternoon)}€')
	littlePriceLabel.set_text(f'{calc(day, month, year, afternoon)}€')

def get_item_stock(day, month, year, article):
	cursor.execute('SELECT articles FROM ventes WHERE date = ?', (f"{year}-{'0' * (2-len(str(month))) + str(month)}-{'0' * (2-len(str(day))) + str(day)}",))
	data = cursor.fetchall()
	if(data == []):
		return 0
	else:
		articles = json.loads(data[0][0])
		try:
			return articles[article]
		except:
			return 0

def calc(day, month, year, afternoon):
	articles = getSelledArticles(day, month, year, afternoon)
	f = open(directory + 'prix_articles.json')
	prix_articles = json.load(f)
	acc = 0
	if(articles != None):
		for article in articles:
			if(article in prix_articles):
				acc += prix_articles[article] * articles[article]
		acc = round(acc, 2)
	return acc

def calc_week():
	monday = current_monday
	tuesday = add_days(monday, 1)
	wednesday = add_days(monday, 2)
	thursday = add_days(monday, 3)
	friday = add_days(monday, 4)
	return calc(monday[0], monday[1], monday[2], 0) + calc(monday[0], monday[1], monday[2], 1) +calc(tuesday[0], tuesday[1], tuesday[2], 0) + calc(tuesday[0], tuesday[1], tuesday[2], 1) + calc(wednesday[0], wednesday[1], wednesday[2], 0) + calc(thursday[0], thursday[1], thursday[2], 0) + calc(thursday[0], thursday[1], thursday[2], 1) + calc(friday[0], friday[1], friday[2], 0) + calc(friday[0], friday[1], friday[2], 1)

def hex_to_rgba(hex_value):
	rgba = Gdk.RGBA()
	rgba.parse(hex_value)
	return rgba

def colorify(object, color):
	css_provider = Gtk.CssProvider()
	css_provider.load_from_data(f"* {{background-color: {color};}}".encode('utf-8'))
	style_context = object.get_style_context()
	style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def boldify(object):
	css_provider = Gtk.CssProvider()
	css_provider.load_from_data("label {font-weight: bold; font-size: 40px;}".encode('utf-8'))
	style_context = object.get_style_context()
	style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def regularify(object):
	css_provider = Gtk.CssProvider()
	css_provider.load_from_data("label {font-weight: normal;}".encode('utf-8'))
	style_context = object.get_style_context()
	style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def get_week_days(day_number, month_number, current_year):
	target_date = datetime(current_year, month_number, day_number)
	monday = target_date - timedelta(days=target_date.weekday())
	week_days = []
	for i in range(5):
		current_day = monday + timedelta(days=i)
		formatted_date = current_day.strftime("%A %d %b")
		week_days.append(formatted_date.capitalize())
	return week_days

def get_current_monday():
	today = datetime.now()
	current_monday = today - timedelta(days=today.weekday())
	day_of_month = current_monday.day
	month_of_year = current_monday.month
	year = current_monday.year
	current_monday = [day_of_month, month_of_year, year]
	return current_monday

def get_previous_monday(input_date):
	input_date_object = datetime(input_date[2], input_date[1], input_date[0])
	previous_monday = input_date_object - timedelta(days=input_date_object.weekday() + 7)
	day_of_month = previous_monday.day
	month_of_year = previous_monday.month
	year = previous_monday.year
	result_list = [day_of_month, month_of_year, year]
	return result_list

def get_next_monday(input_date):
	input_date_object = datetime(input_date[2], input_date[1], input_date[0])
	next_monday = input_date_object + timedelta(days=(7 - input_date_object.weekday()))
	day_of_month = next_monday.day
	month_of_year = next_monday.month
	year = next_monday.year
	result_list = [day_of_month, month_of_year, year]
	return result_list

def add_days(day, delta):
	initial_date = datetime(day[2], day[1], day[0])
	new_date = initial_date + timedelta(days=delta)
	day_res = new_date.day
	month_res = new_date.month
	year_res = new_date.year
	return [day_res, month_res, year_res]

current_monday = get_current_monday()
week_day_labels = []

grid_boxes = [[], []]
colorGrids = [
[
	["#EB5466",
	 "#EB6A54",
	 "#EB8554",
	 "#EB9E54",
	 "#F5C164"],

	["#EB6A54",
	 "#EB8554",
	 "#E3E3E3",
	 "#F5C164",
	 "#F5BA9F"]
],
[
	["#EBB375",
	 "#EBC375",
	 "#EBD176",
	 "#EBDF75",
	 "#EBF587"],

	["#EBC375",
	 "#EBD176",
	 "#E3E3E3",
	 "#EBF587",
	 "#F5EAC1"]
],
[
	["#86EB63",
	 "#63EB74",
	 "#62EBA3",
	 "#63EBD0",
	 "#73E3F5"],

	["#63EB74",
	 "#62EBA3",
	 "#E3E3E3",
	 "#73E3F5",
	 "#a2e7f2"]
],
[
	["#88C8EB",
	 "#88A9EB",
	 "#898AEB",
	 "#A788EB",
	 "#D49AF5"],

	["#88A9EB",
	 "#898AEB",
	 "#E3E3E3",
	 "#D49AF5",
	 "#e3c4f5"]
]
]

littleLabels = [[Gtk.Label(), Gtk.Label(), Gtk.Label(), Gtk.Label(), Gtk.Label()], 
				[Gtk.Label(), Gtk.Label(), Gtk.Label(), Gtk.Label(), Gtk.Label()]]

def update():
	for i in range(len(week_day_labels)):
		week_day_labels[i].set_text(get_week_days(current_monday[0], current_monday[1], current_monday[2])[i])
	for i in range(2):
		for j in range(5):
			colorify(grid_boxes[i][j], colorGrids[(current_monday[0]//7)%4][i][j])
			if(not(i == 1 and j == 2)):
				grid_boxes[i][j].set_sensitive(True)
				littleLabels[i][j].set_text(f'{calc(add_days(current_monday, j)[0], add_days(current_monday, j)[1], add_days(current_monday, j)[2], i)}€')
	button_left.set_sensitive(True)
	button_right.set_sensitive(True)
	button_json.set_sensitive(True)
	button_save.set_sensitive(True)
	button_stock.set_sensitive(True)
	button_supply.set_sensitive(True)

def week_left(button):
	global current_monday
	current_monday = get_previous_monday(current_monday)
	update()

def week_right(button):
	global current_monday
	current_monday = get_next_monday(current_monday)
	update()

def save_file(currentname):
	dialog = Gtk.FileChooserDialog(
		title="Enregistrer le fichier",
		action=Gtk.FileChooserAction.SAVE
	)

	dialog.add_buttons(
		Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		Gtk.STOCK_SAVE, Gtk.ResponseType.OK
	)

	dialog.set_default_response(Gtk.ResponseType.OK)

	# Ajouter un filtre pour autoriser uniquement les fichiers texte (.txt)
	slsx_filter = Gtk.FileFilter()
	slsx_filter.set_name("Excel 2007-365 (.xlsx)")
	slsx_filter.add_pattern("*.xlsx")
	dialog.add_filter(slsx_filter)

	dialog.set_current_name(currentname)

	response = dialog.run()
	file_path = None

	if response == Gtk.ResponseType.OK:
		file_path = dialog.get_filename()
	elif response == Gtk.ResponseType.CANCEL:
		dialog.destroy()
		return None

	dialog.destroy()
	return file_path

def savesheet(self):

	alphabet = ["A", "B", "C", "D", "E", "F", "G", "H"]

	day1 = "0" + str(current_monday[0])
	day1 = day1[-2:]
	day2 = "0" + str(add_days(current_monday, 4)[0])
	day2 = day2[-2:]
 
	month1 = "0" + str(current_monday[1])
	month1 = month1[-2:]
	month2 = "0" + str(add_days(current_monday, 4)[1])
	month2 = month2[-2:]

	path = save_file(f"Recette Cafet {day1}_{month1}_{str(current_monday[2])[-2:]} {day2}_{month2}_{str(add_days(current_monday, 4)[2])[-2:]}")
	if(path == None):
		return
	if(len(path) >= 6):
		if(path[-5:] != ".xlsx"):
			path += ".xlsx"
	else:
		path += ".xlsx"
	shutil.copy(directory + "template.xlsx", path)

	classeur = openpyxl.load_workbook(path)
	feuille = classeur['Sheet1']

	f = open(directory + 'prix_articles.json')
	prix_articles = json.load(f)
	k = 7
	for article in prix_articles:
		price = str(prix_articles[article]).replace(".", ",")
		if(len(price.split(",")[1]) == 1):
			price += "0"
		feuille["A" + str(k)] = f"{article}\n({price} €)"
		feuille["A" + str(k)].alignment = openpyxl.styles.Alignment(wrap_text=True, horizontal='center', vertical='center')
		k += 1
	del k

	monday0 = getSelledArticles(add_days(current_monday, 0)[0], add_days(current_monday, 0)[1], add_days(current_monday, 0)[2], 0)
	monday0 = [] if monday0 == None else monday0
	tuesday0 = getSelledArticles(add_days(current_monday, 1)[0], add_days(current_monday, 1)[1], add_days(current_monday, 1)[2], 0)
	tuesday0 = [] if tuesday0 == None else tuesday0
	wednesday0 = getSelledArticles(add_days(current_monday, 2)[0], add_days(current_monday, 2)[1], add_days(current_monday, 2)[2], 0)
	wednesday0 = [] if wednesday0 == None else wednesday0
	thursday0 = getSelledArticles(add_days(current_monday, 3)[0], add_days(current_monday, 3)[1], add_days(current_monday, 3)[2], 0)
	thursday0 = [] if thursday0 == None else thursday0
	friday0 = getSelledArticles(add_days(current_monday, 4)[0], add_days(current_monday, 4)[1], add_days(current_monday, 4)[2], 0)
	friday0 = [] if friday0 == None else friday0

	monday1 = getSelledArticles(add_days(current_monday, 0)[0], add_days(current_monday, 0)[1], add_days(current_monday, 0)[2], 1)
	monday1 = [] if monday1 == None else monday1
	tuesday1 = getSelledArticles(add_days(current_monday, 1)[0], add_days(current_monday, 1)[1], add_days(current_monday, 1)[2], 1)
	tuesday1 = [] if tuesday1 == None else tuesday1
	wednesday1 = getSelledArticles(add_days(current_monday, 2)[0], add_days(current_monday, 2)[1], add_days(current_monday, 2)[2], 1)
	wednesday1 = [] if wednesday1 == None else wednesday1
	thursday1 = getSelledArticles(add_days(current_monday, 3)[0], add_days(current_monday, 3)[1], add_days(current_monday, 3)[2], 1)
	thursday1 = [] if thursday1 == None else thursday1
	friday1 = getSelledArticles(add_days(current_monday, 4)[0], add_days(current_monday, 4)[1], add_days(current_monday, 4)[2], 1)
	friday1 = [] if friday1 == None else friday1

	week = [[monday0, monday1], [tuesday0, tuesday1], [wednesday0, wednesday1], [thursday0, thursday1], [friday0, friday1]]

	for i in range(5):
		j = 0
		for article in prix_articles:
			try:
				feuille[alphabet[i+1] + str(j+7)] = week[i][0][article]
			except:
				feuille[alphabet[i+1] + str(j+7)] = 0
			try:
				feuille[alphabet[i+1] + str(j+7)] = feuille[alphabet[i+1] + str(j+7)].value + week[i][1][article]
			except:
				pass
			j += 1
		del j
	
	recette = 0

	i = 0
	for article in prix_articles:
		quantity = feuille["B" + str(i+7)].value + feuille["C" + str(i+7)].value + feuille["D" + str(i+7)].value + feuille["E" + str(i+7)].value + feuille["F" + str(i+7)].value
		feuille["G" + str(i+7)] = quantity
		price = quantity * prix_articles[article]
		recette += price
		price = round(price, 2)
		price = str(price).replace(".", ",")
		price = price + "0" if len(price.split(",")[1]) == 1 else price
		feuille["H" + str(i+7)] = price + " €"
		i += 1
	del i

	date = f"{add_days(current_monday, 4)[2]}-{'0' * (2-len(str(add_days(current_monday, 4)[1]))) + str(add_days(current_monday, 4)[1])}-{'0' * (2-len(str(add_days(current_monday, 4)[0]))) + str(add_days(current_monday, 4)[0])}"
	i = 0
	for article in get_stock(date):
		feuille["I" + str(i+7)] = get_stock(date)[article]
		i += 1
	del i

	recette = round(recette, 2)
	recette = str(recette).replace(".", ",")
	recette = recette + "0" if len(recette.split(",")[1]) == 1 else recette
	feuille["H28"] = recette + " €"
	
	feuille["A3"] = f"SEMAINE : DU {day1} / {month1} / {str(current_monday[2])[-2:]}  AU  {day2} / {month2} / {str(add_days(current_monday, 4)[2])[-2:]}"

	classeur.save(path)

def button_clicked(row, column, label, widget):
	global littlePriceLabel
	littlePriceLabel = label
	for i in range(2):
		for j in range(5):
			colorify(grid_boxes[i][j], "#E3E3E3")
			grid_boxes[i][j].set_sensitive(False)
	colorify(grid_boxes[row][column], colorGrids[(current_monday[0]//7)%4][row][column])
	button_left.set_sensitive(False)
	button_right.set_sensitive(False)
	EditActivity(row, column)

def edit_json(self):
	JsonActivity()

def edit_stock(self):
	StockActivity()

def supply(self):
	SupplyActivity()

button_left = Gtk.Button()
button_right = Gtk.Button()
button_save = Gtk.Button()
button_json = Gtk.Button()
button_stock = Gtk.Button()
button_supply = Gtk.Button()

class MainActivity(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="School Cafet Manager")

		# Créer la barre d'en-tête
		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = "School Cafet Manager"
		self.set_titlebar(header_bar)

		css_provider = Gtk.CssProvider()
		css_provider.load_from_data(b"""
			.black-icon {
				color: #000000;
			}
		""")

		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(),
			css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

		# Créer le bouton "Enregistrer" avec l'icône de disquette
		save_icon = Gio.ThemedIcon(name="document-save-symbolic")
		image = Gtk.Image.new_from_gicon(save_icon, Gtk.IconSize.BUTTON)
		image.get_style_context().add_class("black-icon")
		button_save.add(image)
		button_save.connect("clicked", savesheet)
		button_save.set_can_focus(False)
		header_bar.pack_start(button_save)
		
		# Créer le bouton "JSON"
		json_icon = Gio.ThemedIcon(name="preferences-system-symbolic")
		image = Gtk.Image.new_from_gicon(json_icon, Gtk.IconSize.BUTTON)
		image.get_style_context().add_class("black-icon")
		button_json.add(image)
		button_json.connect("clicked", edit_json)
		button_json.set_can_focus(False)
		header_bar.pack_start(button_json)

		# Créer le bouton "Stock"
		stock_icon = Gio.ThemedIcon(name="view-visible")
		image = Gtk.Image.new_from_gicon(stock_icon, Gtk.IconSize.BUTTON)
		image.get_style_context().add_class("black-icon")
		button_stock.add(image)
		button_stock.connect("clicked", edit_stock)
		button_stock.set_can_focus(False)
		header_bar.pack_start(button_stock)

		# Créer le bouton "Approvisionnement"
		supply_icon = Gio.ThemedIcon(name="archive")
		image = Gtk.Image.new_from_gicon(supply_icon, Gtk.IconSize.BUTTON)
		image.get_style_context().add_class("black-icon")
		button_supply.add(image)
		button_supply.connect("clicked", supply)
		button_supply.set_can_focus(False)
		header_bar.pack_start(button_supply)
		
		header_bar.set_size_request(-1, 40)

		self.connect("destroy", Gtk.main_quit)

		overlay = Gtk.Overlay()
		self.add(overlay)

		mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		overlay.add(mainBox)

		# Deuxième grille en haut de la première grille
		grid2 = Gtk.Grid()
		mainBox.pack_start(grid2, False, True, 0)

		# Configuration de la deuxième grille
		grid2.set_column_homogeneous(True)
		grid2.set_column_spacing(5)
		grid2.set_row_homogeneous(True)
		grid2.set_row_spacing(5)

		# Ajout de boutons dans la deuxième grille
		for j in range(5):
			box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
			box.set_margin_top(7)
			box.set_margin_bottom(2)
			
			colorify(box, "#F2F2F2")
			label = Gtk.Label()
			label.set_text(get_week_days(current_monday[0], current_monday[1], current_monday[2])[j])
			box.pack_start(label, True, True, 0)
			grid2.attach(box, j, 0, 1, 1)
			week_day_labels.append(label)  # Ajoute le label à la liste

		# Première grille
		grid1 = Gtk.Grid()
		mainBox.pack_start(grid1, True, True, 0)

		grid1.set_column_homogeneous(True)
		grid1.set_column_spacing(5)
		grid1.set_row_homogeneous(True)
		grid1.set_row_spacing(5)

		# Ajout de boutons dans la première grille
		for i in range(2):
			for j in range(5):
				button = Gtk.Button()
				if not (i == 1 and j == 2):
					label = Gtk.Label()
					label.set_text(f'{calc(add_days(current_monday, j)[0], add_days(current_monday, j)[1], add_days(current_monday, j)[2], i)}€')
					button.add(label)
					littleLabels[i][j] = label
					# Ajoute un gestionnaire d'événements pour le signal "clicked"
					button.connect("clicked", partial(button_clicked, i, j, label))
				else:
					button.set_sensitive(False)
				button.set_can_focus(False)
				context = label.get_style_context()
				context.add_class(Gtk.STYLE_CLASS_DIM_LABEL)
				boldify(label)

				colorify(button, colorGrids[(current_monday[0] // 7) % 4][i][j])
				grid_boxes[i].append(button)
				grid1.attach(button, j, i, 1, 1)

				
		mainBox.set_margin_start(5)
		mainBox.set_margin_end(5)
		mainBox.set_margin_top(5)
		mainBox.set_margin_bottom(5)

		# Ajout du bouton vers la gauche
		button_left.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.LEFT, shadow_type=Gtk.ShadowType.NONE))
		overlay.add_overlay(button_left)
		overlay.set_overlay_pass_through(button_left, True)
		button_left.set_halign(Gtk.Align.START)
		button_left.set_valign(Gtk.Align.START)
		button_left.set_size_request(30, 30)
		button_left.set_margin_top(4)
		button_left.set_margin_start(6)
		colorify(button_left, "#F2F2F2")
		button_left.set_can_focus(False)
		button_left.connect("clicked", week_left)

		# Ajout du bouton vers la droite
		button_right.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.NONE))
		overlay.add_overlay(button_right)
		overlay.set_overlay_pass_through(button_right, True)
		button_right.set_halign(Gtk.Align.END)
		button_right.set_valign(Gtk.Align.START)
		button_right.set_size_request(30, 30)
		button_right.set_margin_top(4)
		button_right.set_margin_end(6)
		colorify(button_right, "#F2F2F2")
		button_right.set_can_focus(False)
		button_right.connect("clicked", week_right)

		self.show_all()
		self.set_size_request(1000, 560)

class EditActivity(Gtk.Window):
	def __init__(self, i, j):
		self.i = i
		self.j = j
		Gtk.Window.__init__(self, title="Editer les ventes")

		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = "Editer les ventes"
		self.set_titlebar(header_bar)

		self.connect("destroy", self.destroy)

		day = add_days(current_monday, self.j)[0]
		month = add_days(current_monday, self.j)[1]
		year = add_days(current_monday, self.j)[2]

		# Création de la grille
		grid = Gtk.Grid()
		grid.set_row_spacing(10)
		grid.set_column_spacing(10)

		f = open(directory + 'prix_articles.json')
		prix_articles = json.load(f)
		# Création des boutons avec des images pour la grille
		for i in range(len(prix_articles)):
			# Définir le répertoire et l'article
			article = list(prix_articles.keys())[i]

			# Création de l'image pour le bouton
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
				filename=f'{directory}Images/{article.replace(" ", "")}.png', 
				width=150, 
				height=150, 
				preserve_aspect_ratio=True
			)
			image_button = Gtk.Image.new_from_pixbuf(pixbuf)

			# Création du popover
			popover = Gtk.Popover()
			popover.set_position(Gtk.PositionType.BOTTOM)

			# Création de la grille pour le popover
			popover_grid = Gtk.Grid()
			popover_grid.set_row_spacing(10)
			popover_grid.set_column_spacing(10)

			# Création des labels séparément
			label_minus = Gtk.Label(label="-")
			label_plus = Gtk.Label(label="+")

			# Application des fonctions boldify et regularify
			boldify(label_minus)
			regularify(label_minus)
			boldify(label_plus)
			regularify(label_plus)

			# Création des boutons et ajout des labels
			quantityLabel = Gtk.Label()
			
			selledArticles = getSelledArticles(day, month, year, self.i)
			if selledArticles == {} or selledArticles == None:
				quantityLabel.set_text("0")
			else:
				quantityLabel.set_text(str(selledArticles[article] if article in selledArticles else 0))
			quantityLabel.set_size_request(150, 150)
			boldify(quantityLabel)

			button_minus = Gtk.Button()
			button_minus.set_size_request(150, 150)
			button_minus.add(label_minus)
			button_minus.connect("clicked", partial(unsellArticle, day, month, year, self.i, article, quantityLabel))

			button_plus = Gtk.Button()
			button_plus.set_size_request(150, 150)
			button_plus.add(label_plus)
			button_plus.connect("clicked", partial(sellArticle, day, month, year, self.i, article, quantityLabel))

			# Ajout des boutons à la grille du popover
			popover_grid.attach(button_minus, 0, 0, 1, 1)
			popover_grid.attach(quantityLabel, 1, 0, 1, 1)
			popover_grid.attach(button_plus, 2, 0, 1, 1)

			# Ajout de la vbox du popover
			popover_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
			
			popover_price_label = Gtk.Label()
			f = open(directory + 'prix_articles.json')
			prix_articles = json.load(f)
			price = str(prix_articles[article]).replace(".", ",")
			popover_price_label.set_text(f"{price}0€")
			popover_price_label.set_margin_top(10)
			
			popover_vbox.add(popover_price_label)
			popover_grid.set_margin_bottom(5)
			popover_vbox.add(popover_grid)
			
			# Ajout de la grille au popover
			popover.add(popover_vbox)
			popover.show_all()
			popover.hide()

			# Bouton MenuButton pour afficher le popover avec une image
			button = Gtk.MenuButton(popover=popover)
			button.set_image(image_button)
			button.set_size_request(150, 150)
			button.set_margin_bottom(5)
			button.set_margin_end(5)
			button.set_margin_start(5)
			button.set_hexpand(True)

			# Ajout du bouton à la grille
			grid.attach(button, i%6, i//6, 1, 1)

		# Création d'une fenêtre avec défilement
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrolled_window.add(grid)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		self.add(vbox)

		# Ajout de la fenêtre avec défilement directement à la fenêtre principale
		vbox.pack_start(scrolled_window, True, True, 0)

		# Big Price Button
		button = Gtk.Button()
		label = Gtk.Label()
		label.set_text(f'{calc(day, month, year, self.i)}€')
		global bigPriceLabel
		bigPriceLabel = label
		button.add(label)
		button.set_can_focus(False)
		context = label.get_style_context()
		context.add_class(Gtk.STYLE_CLASS_DIM_LABEL)
		boldify(label)
		colorify(button, colorGrids[(current_monday[0] // 7) % 4][self.i][self.j])
		button.set_size_request(-1, 100)
		button.set_margin_bottom(5)
		button.set_margin_end(5)
		button.set_margin_start(5)
		vbox.pack_start(button, False, True, 0)

		self.show_all()
		self.set_size_request(1250, 620)

	def on_plus_clicked(self, button):
		print("Plus button clicked!")

	def on_minus_clicked(self, button):
		print("Minus button clicked!")

	def destroy(self, widget):
		update()

nameinputs = {}
priceinputs = {}
filenameLabels = {}
prix_articles = {}
subgrids = {}
buttons_delete = {}
delete_handlers = {}
modify_handlers = {}
buttons_subvalidate = {}
subvalidate_handlers = {}
vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

def delete(article, widget):
	del nameinputs[article]
	del priceinputs[article]
	del filenameLabels[article]
	del prix_articles[article]
	del buttons_delete[article]
	vbox2.remove(subgrids[article])

def premodify(article, widget, event):
	global buttons_subvalidate
	global subvalidate_handlers
	if event.keyval == Gdk.KEY_Return:
		modify(article, None)
	else:
		if(filenameLabels[article].get_text() == nameinputs[article].get_text().replace(" ", "") + ".png"):
			buttons_subvalidate[article].set_sensitive(False)
			colorify(buttons_subvalidate[article], "#dedede")
		else:
			buttons_subvalidate[article].set_sensitive(True)
			colorify(buttons_subvalidate[article], "#0090ed")

def modify(article, widget):
	global nameinputs
	global priceinputs
	global filenameLabels
	global prix_articles
	global subgrids
	global buttons_delete
	global delete_handlers
	global buttons_subvalidate
	global subvalidate_handlers
	buttons_subvalidate[article].set_sensitive(False)
	colorify(buttons_subvalidate[article], "#dedede")
	new_article = nameinputs[article].get_text()
	if(article != new_article):
		if(new_article in prix_articles):
			nameinputs[article].set_text(article)
		else:
			nameinputs[new_article] = nameinputs[article]
			del nameinputs[article]
			nameinputs[new_article].disconnect(modify_handlers[article])
			del modify_handlers[article]
			modify_handlers[new_article] = nameinputs[new_article].connect("key-release-event", partial(premodify, new_article))
			priceinputs[new_article] = priceinputs[article]
			del priceinputs[article]
			filenameLabels[new_article] = filenameLabels[article]
			del filenameLabels[article]
			filenameLabels[new_article].set_text(new_article.replace(" ", "") + ".png")
			prix_articles[new_article] = prix_articles[article]
			del prix_articles[article]
			subgrids[new_article] = subgrids[article]
			del subgrids[article]
			buttons_delete[new_article] = buttons_delete[article]
			del buttons_delete[article]
			buttons_delete[new_article].disconnect(delete_handlers[article])
			del delete_handlers[article]
			delete_handlers[new_article] = buttons_delete[new_article].connect("clicked", partial(delete, new_article))
			buttons_subvalidate[new_article] = buttons_subvalidate[article]
			del buttons_subvalidate[article]
			buttons_subvalidate[new_article].disconnect(subvalidate_handlers[article])
			del subvalidate_handlers[article]
			subvalidate_handlers[new_article] = buttons_subvalidate[new_article].connect("clicked", partial(modify, new_article))

class JsonActivity(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="Configurer le logiciel")

		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = "Configurer le logiciel"
		self.set_titlebar(header_bar)

		self.connect("destroy", self.destroy)
		
		global nameinputs
		global priceinputs
		global filenameLabels
		global prix_articles
		global subgrids
		global vbox2
		global buttons_delete
		global delete_handlers
		global modify_handlers
		global buttons_subvalidate
		global subvalidate_handlers
		
		nameinputs = {}
		priceinputs = {}
		filenameLabels = {}
		subgrids = {}
		buttons_delete = {}
		delete_handlers = {}
		modify_handlers = {}
		buttons_subvalidate = {}
		subvalidate_handlers = {}
		vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		
		for i in range(2):
			for j in range(5):
				colorify(grid_boxes[i][j], "#F2F2F2")
				grid_boxes[i][j].set_sensitive(False)
		button_left.set_sensitive(False)
		button_right.set_sensitive(False)
		button_json.set_sensitive(False)
		button_save.set_sensitive(False)
		button_stock.set_sensitive(False)
		button_supply.set_sensitive(False)
		
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		
		grid = Gtk.Grid()	
		grid.set_column_homogeneous(True)
		grid.set_column_spacing(5)
		grid.set_row_homogeneous(True)
		grid.set_row_spacing(5)
		grid.set_size_request(-1, 40)
		colorify(grid, "#F2F2F2")
		vbox.pack_start(grid, False, True, 0)
		
		label = Gtk.Label()
		label.set_text("Article")
		grid.attach(label, 0, 0, 1, 1)
		label = Gtk.Label()
		label.set_text("Prix (€)")
		grid.attach(label, 1, 0, 1, 1)
		label = Gtk.Label()
		label.set_text("Fichier image")
		grid.attach(label, 3, 0, 1, 1)
		
		scrollview = Gtk.ScrolledWindow()
		scrollview.add(vbox2)
		scrollview.set_margin_start(5)
		scrollview.set_margin_end(5)
		vbox.pack_start(scrollview, True, True, 0)
		
		
		f = open(directory + 'prix_articles.json')
		prix_articles = json.load(f)
		
		for article in prix_articles:
			subgrid = Gtk.Grid()
			subgrid.set_column_homogeneous(True)
			subgrid.set_column_spacing(5)
			subgrid.set_row_homogeneous(True)
			subgrid.set_column_spacing(5)
			subgrid.set_size_request(-1, 40)
			vbox2.pack_start(subgrid, False, True, 0)
			
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
			#
			button_delete = Gtk.Button()
			delete_icon = Gio.ThemedIcon(name="list-remove-symbolic")
			image = Gtk.Image.new_from_gicon(delete_icon, Gtk.IconSize.BUTTON)
			button_delete.add(image)
			delete_handlers[article] = button_delete.connect("clicked", partial(delete, article))
			button_delete.set_can_focus(False)
			colorify(button_delete, "#ff4d4d")
			buttons_delete[article] = button_delete
			hbox.pack_start(button_delete, False, True, 0)
			#
			nameinputs[article] = Gtk.Entry()
			nameinputs[article].set_text(article)
			modify_handlers[article] = nameinputs[article].connect("key-release-event", partial(premodify, article))
			hbox.pack_start(nameinputs[article], True, True, 0)
			#
			subgrid.attach(hbox, 0, 0, 1, 1)
			
			priceinputs[article] = Gtk.Entry()
			priceinputs[article].set_text(str(prix_articles[article]))
			subgrid.attach(priceinputs[article], 1, 0, 1, 1)
			
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
			#
			filename = article.replace(" ", "") + ".png"
			filenameLabels[article] = Gtk.Entry()
			filenameLabels[article].set_editable(False)
			filenameLabels[article].set_text(filename)
			hbox.pack_start(filenameLabels[article], True, True, 0)
			#
			button_subvalidate = Gtk.Button()
			subvalidate_icon = Gio.ThemedIcon(name="document-edit-symbolic")
			image = Gtk.Image.new_from_gicon(subvalidate_icon, Gtk.IconSize.BUTTON)
			button_subvalidate.add(image)
			subvalidate_handlers[article] = button_subvalidate.connect("clicked", partial(modify, article))
			button_subvalidate.set_can_focus(False)
			colorify(button_subvalidate, "#dedede")
			button_subvalidate.set_sensitive(False)
			buttons_subvalidate[article] = button_subvalidate
			hbox.pack_start(button_subvalidate, False, True, 0)
			#
			subgrid.attach(hbox, 3, 0, 1, 1)
			
			subgrids[article] = subgrid
		
		
		
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		button_add = Gtk.Button()
		label_add = Gtk.Label()
		label_add.set_text("Ajouter")
		button_add.add(label_add)
		button_add.set_margin_bottom(5)
		button_add.connect("clicked", partial(self.add_article, scrollview))
		hbox.pack_start(button_add, False, True, 5)
		button_validate = Gtk.Button()
		label_validate = Gtk.Label()
		label_validate.set_text("Valider")
		button_validate.add(label_validate)
		button_validate.set_margin_bottom(5)
		button_validate.connect("clicked", self.validate)
		hbox.pack_end(button_validate, False, True, 5)
		vbox.pack_start(hbox, False, True, 0)
		
		self.add(vbox)
		
		self.show_all()
		self.set_size_request(1000, 560)
	
	def refresh(self):
		for article in prix_articles:
			filenameLabels[article].set_text(nameinputs[article].get_text().replace(" ", "") + ".png")
	
	def add_article(self, scrollview, widget):
		global nameinputs
		global priceinputs
		global filenameLabels
		global prix_articles
		global subgrids
		global vbox2
		global buttons_delete
		global delete_handlers
		global modify_handlers
		global buttons_subvalidate
		global subvalidate_handlers
		
		article = "Article " + str(len(prix_articles) + 1)
		prix_articles[article] = 0.0
		
		subgrid = Gtk.Grid()
		subgrid.set_column_homogeneous(True)
		subgrid.set_column_spacing(5)
		subgrid.set_row_homogeneous(True)
		subgrid.set_column_spacing(5)
		subgrid.set_size_request(-1, 40)
		vbox2.pack_start(subgrid, False, True, 0)
				
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		#
		button_delete = Gtk.Button()
		delete_icon = Gio.ThemedIcon(name="list-remove-symbolic")
		image = Gtk.Image.new_from_gicon(delete_icon, Gtk.IconSize.BUTTON)
		button_delete.add(image)
		delete_handlers[article] = button_delete.connect("clicked", partial(delete, article))
		button_delete.set_can_focus(False)
		colorify(button_delete, "#ff4d4d")
		buttons_delete[article] = button_delete
		hbox.pack_start(button_delete, False, True, 0)
		#
		nameinputs[article] = Gtk.Entry()
		nameinputs[article].set_text(article)
		modify_handlers[article] = nameinputs[article].connect("key-release-event", partial(premodify, article))
		hbox.pack_start(nameinputs[article], True, True, 0)
		#
		subgrid.attach(hbox, 0, 0, 1, 1)
		
		priceinputs[article] = Gtk.Entry()
		priceinputs[article].set_text(str(prix_articles[article]))
		subgrid.attach(priceinputs[article], 1, 0, 1, 1)
		
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		#
		filename = article.replace(" ", "") + ".png"
		filenameLabels[article] = Gtk.Entry()
		filenameLabels[article].set_text(filename)
		filenameLabels[article].set_editable(False)
		hbox.pack_start(filenameLabels[article], True, True, 0)
		#
		button_subvalidate = Gtk.Button()
		subvalidate_icon = Gio.ThemedIcon(name="document-edit-symbolic")
		image = Gtk.Image.new_from_gicon(subvalidate_icon, Gtk.IconSize.BUTTON)
		button_subvalidate.add(image)
		subvalidate_handlers[article] = button_subvalidate.connect("clicked", partial(modify, article))
		button_subvalidate.set_can_focus(False)
		colorify(button_subvalidate, "#dedede")
		button_subvalidate.set_sensitive(False)
		buttons_subvalidate[article] = button_subvalidate
		hbox.pack_start(button_subvalidate, False, True, 0)
		#
		subgrid.attach(hbox, 3, 0, 1, 1)
		
		subgrids[article] = subgrid
		self.show_all()
		
		dialog = Gtk.MessageDialog(
			parent=self,
			flags=0,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.OK,
			text=f'{article} ajouté à la liste.'
		)

		dialog.connect("response", self.on_dialog_response)
		dialog.show_all()
	
	def validate(self, widget):
		global prix_articles
		for article in prix_articles:
			prix_articles[article] = float(priceinputs[article].get_text())
		with open(directory + 'prix_articles.json', 'w') as prix_articles_json:
				json.dump(prix_articles, prix_articles_json, indent=4)
		
		dialog = Gtk.MessageDialog(
			parent=self,
			flags=0,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.OK,
			text=f'Paramètres enregistrés.'
		)
		dialog.connect("response", self.on_dialog_response)
		dialog.show_all()
	
	def on_dialog_response(self, widget, response_id):
		widget.destroy()
	
	def destroy(self, widget):
		update()

def get_stock(date):
	cursor.execute('SELECT articles FROM approvisionnements WHERE date <= ?', (date,))
	approvisionnements = cursor.fetchall()
	cursor.execute('SELECT articles FROM ventes WHERE date <= ?', (date,))
	ventes = cursor.fetchall()

	f = open(directory + 'prix_articles.json')
	stock = json.load(f)
	for i in stock:
		stock[i] = 0

	for approvisionnement in approvisionnements:
		for i in json.loads(approvisionnement[0]):
			if(i in stock):
				stock[i] += json.loads(approvisionnement[0])[i]
	for vente in ventes:
		for i in json.loads(vente[0]):
			if(i in stock):
				stock[i] -= json.loads(vente[0])[i]
	
	return stock

stockgrid = Gtk.Grid()
class StockActivity(Gtk.Window):
	def __init__(self):
		global stockgrid
		Gtk.Window.__init__(self, title="Stock")

		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = "Stock"
		self.set_titlebar(header_bar)

		self.connect("destroy", self.destroy)

		for i in range(2):
			for j in range(5):
				colorify(grid_boxes[i][j], "#F2F2F2")
				grid_boxes[i][j].set_sensitive(False)
		button_left.set_sensitive(False)
		button_right.set_sensitive(False)
		button_json.set_sensitive(False)
		button_save.set_sensitive(False)
		button_stock.set_sensitive(False)
		button_supply.set_sensitive(False)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		self.add(vbox)

		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)  # Défilement vertical automatique
		vbox.pack_start(scrolled_window, True, True, 0)

		for child in stockgrid.get_children():
			stockgrid.remove(child)
		stockgrid.set_row_spacing(10)
		stockgrid.set_column_spacing(10)
		scrolled_window.add(stockgrid)

		stock = get_stock(datetime.today().strftime('%Y-%m-%d'))
		i = 0
		for article in stock:
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing = 10)
			hbox.set_hexpand(True)
			stockgrid.attach(hbox, i%3, i//3, 1, 1)

			clearbox = Gtk.Box()
			hbox.pack_start(clearbox, True, True, 0)

			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
				filename=f'{directory}Images/{article.replace(" ", "")}.png', 
				width=128, 
				height=128, 
				preserve_aspect_ratio=True)
			image = Gtk.Image.new_from_pixbuf(pixbuf)
			hbox.pack_start(image, True, True, 0)

			quantityLabel = Gtk.Label(label=str(stock[article]))

			if(stock[article] < 0):
				css_provider = Gtk.CssProvider()
				css_provider.load_from_data(b"""
				label {
					color: red;
				}
				""")
				style_context = quantityLabel.get_style_context()
				style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

			boldify(quantityLabel)
			hbox.pack_start(quantityLabel, True, True, 0)

			clearbox = Gtk.Box()
			hbox.pack_start(clearbox, True, True, 0)

			i += 1
		del i

		self.calendar = Gtk.Calendar()
		colorify(self.calendar, "#d0d0d0")
		self.calendar.connect("day-selected", self.on_day_selected)
		vbox.pack_start(self.calendar, False, True, 0)

		self.show_all()
		self.set_size_request(1000, 560)
	
	def on_day_selected(self, widget):
		year, month, day = self.calendar.get_date()
		for child in stockgrid.get_children():
			stockgrid.remove(child)
		stock = get_stock(f"{year}-{'0' * (2-len(str(month))) + str(month+1)}-{'0' * (2-len(str(day))) + str(day)}")
		i = 0
		for article in stock:
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing = 10)
			hbox.set_hexpand(True)
			stockgrid.attach(hbox, i%3, i//3, 1, 1)

			clearbox = Gtk.Box()
			hbox.pack_start(clearbox, True, True, 0)

			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
				filename=f'{directory}Images/{article.replace(" ", "")}.png', 
				width=128, 
				height=128, 
				preserve_aspect_ratio=True)
			image = Gtk.Image.new_from_pixbuf(pixbuf)
			hbox.pack_start(image, True, True, 0)

			quantityLabel = Gtk.Label(label=str(stock[article]))
			
			if(stock[article] < 0):
				css_provider = Gtk.CssProvider()
				css_provider.load_from_data(b"""
				label {
					color: red;
				}
				""")
				style_context = quantityLabel.get_style_context()
				style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

			boldify(quantityLabel)
			hbox.pack_start(quantityLabel, True, True, 0)

			clearbox = Gtk.Box()
			hbox.pack_start(clearbox, True, True, 0)

			i += 1
		del i
		stockgrid.show_all()

	def destroy(self, widget):
		update()

class SupplyActivity(Gtk.Window):
	def __init__(self):
		global stockgrid
		Gtk.Window.__init__(self, title="Approvisionnements")

		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = "Approvisionnements"
		self.set_titlebar(header_bar)

		self.connect("destroy", self.destroy)

		scrolledWindow = Gtk.ScrolledWindow()
		self.add(scrolledWindow)

		for i in range(2):
			for j in range(5):
				colorify(grid_boxes[i][j], "#F2F2F2")
				grid_boxes[i][j].set_sensitive(False)
		button_left.set_sensitive(False)
		button_right.set_sensitive(False)
		button_json.set_sensitive(False)
		button_save.set_sensitive(False)
		button_stock.set_sensitive(False)
		button_supply.set_sensitive(False)

		self.grid = Gtk.Grid()
		scrolledWindow.add(self.grid)

		self.grid.set_row_spacing(10)
		self.grid.set_margin_top(20)
		self.grid.set_margin_bottom(20)
		self.grid.set_margin_start(20)
		self.grid.set_margin_end(20)

		self.init_grid()

		self.show_all()
		self.set_size_request(1000, 560)

	def init_grid(self, widget=None):
		self.selected_date = datetime.today().strftime('%Y-%m-%d')
		for child in self.grid.get_children():
			self.grid.remove(child)
		f = open(directory + 'prix_articles.json')
		articles = list(json.load(f).keys())
		for article in articles:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
				filename=f'{directory}Images/{article.replace(" ", "")}.png', 
				width=64, 
				height=64, 
				preserve_aspect_ratio=True)
			image = Gtk.Image.new_from_pixbuf(pixbuf)
			image.set_hexpand(True)
			self.grid.attach(image, articles.index(article) + 1, 0, 1, 1)
		
		f = open(directory + 'prix_articles.json')
		self.entries = json.load(f)
		for article in articles:
			self.entries[article] = Gtk.Entry()
			colorify(self.entries[article], "#d0d0d0")
			self.entries[article].set_size_request(-1, 50)
			self.entries[article].set_width_chars(3)
			self.entries[article].set_alignment(0.5)
			self.entries[article].set_text("0")
			self.grid.attach(self.entries[article], articles.index(article) + 1, 1, 1, 1)
			
		self.calendar = Gtk.Calendar()
		self.calendar.connect("day-selected", self.on_day_selected)
		self.grid.attach(self.calendar, 1, 2, len(articles), 1)

		supplyButton = Gtk.Button(label="Approvisionner")
		supplyButton.connect("clicked", self.supply)
		self.grid.attach(supplyButton, 1, 3, len(articles), 1)

		cursor.execute('SELECT * FROM approvisionnements ORDER BY date DESC', ())
		approvisionnements = cursor.fetchall()
		for approvisionnement in approvisionnements:
			date = approvisionnement[0]
			date = date[8:10] + "/" + date[5:7] + "/" + date[0:4]
			label = Gtk.Label(label=date)
			if(approvisionnements.index(approvisionnement) % 2 == 1):
				colorify(label, "#d0d0d0")
				label.set_size_request(-1, 50)
			else:
				label.set_size_request(-1, 30)
			self.grid.attach(label, 0, approvisionnements.index(approvisionnement) + 4, 1, 1)
			for article in articles:
				if(article in json.loads(approvisionnement[1])):
					if(json.loads(approvisionnement[1])[article] > 0):
						string = "+"
						string += str(json.loads(approvisionnement[1])[article])
					elif(json.loads(approvisionnement[1])[article] == 0):
						string = "—"
					else:
						string += str(json.loads(approvisionnement[1])[article])
					label = Gtk.Label(label=string)
				else:
					label = Gtk.Label(label="—")
				if(approvisionnements.index(approvisionnement) % 2 == 1):
					colorify(label, "#d0d0d0")
					label.set_size_request(-1, 50)
				else:
					label.set_size_request(-1, 30)
				self.grid.attach(label, articles.index(article) + 1, approvisionnements.index(approvisionnement) + 4, 1, 1)
		self.grid.show_all()

	def supply(self, widget):
		f = open(directory + 'prix_articles.json')
		articles = json.load(f)

		for entry in self.entries:
			try:
				number = int(self.entries[entry].get_text())
				if(number == 0):
					del articles[entry]
				else:
					articles[entry] = number
			except:
				del articles[entry]

		if(len(articles) == 0):
			cursor.execute('DELETE FROM approvisionnements WHERE date = ?', (self.selected_date, ))
		else:
			cursor.execute('SELECT * FROM approvisionnements WHERE date = ?', (self.selected_date,))
			if(len(cursor.fetchall()) == 0):
				cursor.execute('INSERT INTO approvisionnements (date, articles) VALUES (?, ?)', (self.selected_date, json.dumps(articles)))
			else:
				cursor.execute('UPDATE approvisionnements SET articles = ? WHERE date = ?', (json.dumps(articles), self.selected_date))
		db.commit()
		self.init_grid()

	def on_day_selected(self, widget):
		year, month, day = self.calendar.get_date()
		self.selected_date = f"{year}-{'0' * (2-len(str(month))) + str(month+1)}-{'0' * (2-len(str(day))) + str(day)}"

	def destroy(self, widget):
		update()

if __name__ == "__main__":
	app = MainActivity()
	Gtk.main()
	db.close()