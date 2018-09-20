#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

###################################################
# pyramidage
# script pour une de pyramide des âges tout
# catégories à la demande
# données sous forme de fichier texte
# une colonne avec les années de naissance
# une colonne avec les statuts (ita, chercheur...)
# une colonne avec le sexe (F ou H)
# séparateur de colonne au choix
###################################################

###################################################
# UMR 5319 Passages, CNRS
# Pôle Analyse et Représentation des Données
# contact julie.pierson@cnrs.fr
# www.passages.cnrs.fr
###################################################

import sys
from PyQt4 import QtCore, QtGui
from ui_pyramidage import Ui_pyramidAgeDialog
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import datetime


# Initialise la variable globale du numéro de figure, pour pouvoir en créer plusieurs ensuite
num_fig = 0
# Initialise la variable globale de la liste des statuts possibles
liste_statut = []
# Initialise la variable globale de la liste des lignes  du fichier
liste_ligne = []
# recupere l'annee courante
current_year = datetime.datetime.now().year


# Crée le type de bouton spécial qui servira à sélectionner une couleur
class ColorButton(QtGui.QPushButton):
    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent)
        # Rend le bouton plat (pas d'effet de relief)
        self.setFlat(True)
        # Par défaut, la couleur choisie est le gris
        couleur = QtGui.QColor(200, 200, 200)
        # Crée une palette
        palette = QtGui.QPalette()
        # Remplit la palette par la couleur
        palette.setColor(QtGui.QPalette.Button, couleur)
        # Applique la palette au bouton
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        # Quand on clique sur ce type de bouton, ouvre la fenêtre de choix de couleur
        self.clicked.connect(self.showColorDialog)

    # Pour le choix de la couleur
    def showColorDialog(self):        
        couleur = QtGui.QColorDialog.getColor()

        if couleur.isValid():
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Button, couleur)
            self.setPalette(palette)


class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_pyramidAgeDialog()
        self.ui.setupUi(self)
        # pour que la fenêtre soit scrollable
        mainWidget = QtGui.QWidget()
        ##mainWidget.setGeometry(QtCore.QRect(40, 31, 671, 735))
        mainWidget.setLayout(self.ui.formLayout)
        scrollWidget = QtGui.QScrollArea()
        scrollWidget.setWidget(mainWidget)
        scrollWidget.setWidgetResizable(True)
        self.setCentralWidget(scrollWidget)
        # fixe la taille des colonnes du tableau de statuts
        self.ui.statutTableWidget.setColumnWidth(0,200)
        self.ui.statutTableWidget.setColumnWidth(1,150)
        self.ui.statutTableWidget.setColumnWidth(2,150)
        self.ui.statutTableWidget.setFixedWidth(500)
        # rend possible la sélection de plusieurs lignes contigues à la fois dans le tableau de statuts
        self.ui.statutTableWidget.setSelectionBehavior(QtGui.QTableWidget.SelectRows)
        self.ui.statutTableWidget.setSelectionMode(QtGui.QTableWidget.ContiguousSelection)
        # Quand on clique sur le bouton de choix du fichier txt, fait appel a la fonction selectFile
        QtCore.QObject.connect(self.ui.chooseTextFileButton, QtCore.SIGNAL("clicked()"), self.selectFile )
        # Quand on modifie la taille d'une classe d'âge, met à jour la liste pour la dernière classe
        QtCore.QObject.connect(self.ui.tailleClasseSpinBox, QtCore.SIGNAL("valueChanged(int)"),self.updateFinClasse)
        # Quand on modifie la première classe, met à jour la liste pour la dernière classe
        QtCore.QObject.connect(self.ui.debClasseSpinBox, QtCore.SIGNAL("valueChanged(int)"),self.updateFinClasse)
        # Quand on choisit le délimiteur, met à jour l'aperçu du fichier txt
        QtCore.QObject.connect(self.ui.carDelComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateDelimiteur)
        # Quand on choisit le champ statut, met à jour le tableau correspondant
        QtCore.QObject.connect(self.ui.statutComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeStatut)
        # Quand on clique sur le bouton "ajouter un statut", rajouter une ligne dans la table idoine
        QtCore.QObject.connect(self.ui.addStatutPushButton, QtCore.SIGNAL("clicked()"), self.addStatut )
        # Quand on clique sur le bouton "supprimer un statut", supprime la ligne sélectionnée
        QtCore.QObject.connect(self.ui.removeStatutPushButton, QtCore.SIGNAL("clicked()"), self.removeStatut )
        # Quand on clique sur ok, ça lance la fonction ok qui fait tout le travail
        QtCore.QObject.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.ok )
        # Quand on clique sur quitter, ça quitte...
        QtCore.QObject.connect(self.ui.quitButton, QtCore.SIGNAL("clicked()"), self.quitter )
        # indique l'année en cours dans la liste déroulante correspondante
        self.ui.anneeSpinBox.setValue(current_year)

    # Quand on clique sur annuler
    def quitter(self):
        sys.exit()

    # Met à jour la liste déroulante pour la dernière classe d'âge
    def updateFinClasse(self):
        self.ui.finClasseComboBox.clear()
        deb_cl = self.ui.debClasseSpinBox.value()
        taille_cl = self.ui.tailleClasseSpinBox.value()
        liste_fin_cl = []
        i = 1
        # on part du principe qu'on ne veut pas de classe d'âge supérieure à 150
        while deb_cl + taille_cl * i <= 150:
            liste_fin_cl.append(str(deb_cl + taille_cl * i))
            i = i + 1
        # met quand même une valeur dans liste_fin_cl si les valeurs choisies font que la liste est vide
        if liste_fin_cl == []:
            liste_fin_cl.append(str(deb_cl + taille_cl))
        self.ui.finClasseComboBox.addItems(liste_fin_cl)
        # choisit la valeur courante de la liste (autour de 65)
        self.ui.finClasseComboBox.setCurrentIndex(liste_fin_cl.index(str(65 - (65 - deb_cl)%taille_cl)))

    # Remplit le LineEdit par le fichier choisi lors du FileDialog (qui s'affiche donc)
    def selectFile(self):
        nom_fichier = QtGui.QFileDialog.getOpenFileName()
        # si l'utilisateur n'a pas cliqué sur annuler
        if nom_fichier != '':
            # met à jour la ligne où s'affiche le chemin du fichier
            self.ui.textFileLineEdit.setText(nom_fichier)
            # On vérifie que le fichier n'est pas vide
            global liste_ligne
            liste_ligne = self.readFile()
            # Si ce n'est pas vide
            if len(self.readFile()) > 1:
                # ajoute une ligne dans la table des statuts
                self.ui.statutTableWidget.setRowCount(1)
                # met à jour l'aperçu du fichier texte
                self.updatePreview()
                # met à jour les listes déroulantes pour le choix des colonnes
                self.defaultValue(self.ui.anneeNaissComboBox, ['année', 'annee', 'date'], -1)
                self.defaultValue(self.ui.statutComboBox, ['-- tous --', 'statut'], '-- Tous --')
                self.defaultValue(self.ui.sexeComboBox, ['sexe'], -1)
            # Si c'est vide
            else:
                self.ui.textFileLineEdit.setText('')
                self.ui.statutTableWidget.setRowCount(0)
                self.ui.apercuTableWidget.clear()
                self.ui.apercuTableWidget.setRowCount(0)
                self.ui.apercuTableWidget.setColumnCount(0)
                QtGui.QMessageBox.warning(self,'fichier vide','Le fichier choisi ne comporte pas de données.')
                
    # Lecture du fichier texte
    def readFile(self):
        # Va chercher la valeur du caractère délimiteur grâce à la fonction dédiée
        sep_car = self.caractereSeparateur()
        # Lit le contenu du fichier texte
        liste_ligne = []
        for line in open(self.ui.textFileLineEdit.text()).readlines():
            # on ajoute à la liste chaque ligne moins le saut de ligne \n s'il y en a un (rstrip)
            liste_ligne.append(line.rstrip())
        liste_ligne = [i.split(sep_car) for i in liste_ligne]
        # renvoie le contenu du fichier
        return liste_ligne

    # Affiche les valeurs par défaut pour une liste déroulante donnée
    def defaultValue(self, combobox, liste_val, valeur_en_plus):
        # Récupère le contenu du fichier texte
        global liste_ligne
        nom_colonnes = liste_ligne[0]
        # Ajoute la valeur en plus si différente de -1
        if valeur_en_plus != -1:
            nom_colonnes.append(valeur_en_plus)
        # Remet la liste à zéro
        combobox.clear()
        # Remplit la liste par les colonnes du fichier texte
        combobox.addItems(nom_colonnes)
        # Essaye de trouver la bonne valeur en se basant sur liste_val
        for i in nom_colonnes:
            for j in liste_val:
                if (i.lower().find(j) != -1) and combobox.currentIndex() == 0:
                    combobox.setCurrentIndex(nom_colonnes.index(i))

    # Définit la valeur du caractère séparateur à partir de la valeur choisie dans la liste
    def caractereSeparateur(self):
        # liste des valeurs visibles dans la liste
        liste_entree = ['Tabulation','Virgule','Point-virgule','Espace']
        # liste des valeurs correspondantes
        liste_sortie = ['\t',',',';',' ']
        # on en déduit sep_car
        sep_car = liste_sortie[liste_entree.index(self.ui.carDelComboBox.currentText())]
        return sep_car

    # Quand on change le caractère délimiteur
    def updateDelimiteur(self):
        # met à jour l'aperçu du fichier texte
        self.updatePreview()
        # met à jour les listes déroulantes pour le choix des colonnes
        if self.ui.textFileLineEdit.text() != '':
            self.defaultValue(self.ui.anneeNaissComboBox, ['année', 'annee', 'date'], -1)
            self.defaultValue(self.ui.statutComboBox, ['-- tous --', 'statut'], '-- Tous --')
            self.defaultValue(self.ui.sexeComboBox, ['sexe'], -1)
                    
    # Mise à jour de l'aperçu du fichier texte
    def updatePreview(self):
        if self.ui.textFileLineEdit.text() != '':
            # par précaution, on vide la table
            self.ui.apercuTableWidget.clear()
            # on récupère le contenu du fichier texte
            global liste_ligne
            liste_ligne = self.readFile()
            # définition du nombre de colonnes
            self.ui.apercuTableWidget.setColumnCount(len(liste_ligne[0]))
            # définition des noms des colonnes
            self.ui.apercuTableWidget.setHorizontalHeaderLabels(liste_ligne[0])
            # définition du nombre de lignes
            self.ui.apercuTableWidget.setRowCount(len(liste_ligne) - 1)
            # remplissage des lignes
            for i, row in enumerate(liste_ligne[1:]):
                for j, col in enumerate(row):
                    item = QtGui.QTableWidgetItem(col)
                    self.ui.apercuTableWidget.setItem(i, j, item)

    # Mise à jour de la liste des statuts possibles dans le tableau
    def updateListeStatut(self):
        global liste_statut
        # réinitialisation de la liste des statuts possibles
        liste_statut = []
        # récupère le contenu du fichier texte
        global liste_ligne
        # Si aucun statut n'est choisi :
        if self.ui.statutComboBox.currentText() == '-- Tous --':
            # désactive les boutons pour ajouter ou supprimer un statut
            self.ui.addStatutPushButton.setEnabled(False)
            self.ui.removeStatutPushButton.setEnabled(False)   
        # Si un statut est choisi
        else:
            # Reactive les boutons pour ajouter ou supprimer un statut au cas où
            self.ui.addStatutPushButton.setEnabled(True)
            self.ui.removeStatutPushButton.setEnabled(True)
            # parcourt le fichier texte
            for i in  liste_ligne[1:]:
                try:
                    # si on trouve un statut qui n'est pas encore dans la liste
                    if i[(self.ui.statutComboBox.currentIndex())] not in liste_statut:
                        # on l'ajoute à liste_statut
                        liste_statut.append(i[(self.ui.statutComboBox.currentIndex())])
                # en cas d'erreur, on passe à la ligne suivante
                except IndexError:
                    continue         

    # Ajout d'une nouvelle ligne à la table des statuts
    def addLineStatut(self, num_ligne):
        global liste_statut
        # ajoute une ligne vide au tableau à la position demandée
        self.ui.statutTableWidget.insertRow(num_ligne)
        # Si aucun statut n'est choisi :
        if liste_statut == []:
            liste_statut = ['-- Tous --']
        # Crée une liste déroulante vide
        item = QtGui.QComboBox()            
        # ajoute à cette liste les différents statuts
        item.addItems(liste_statut)
        # Crée un bouton pour choisir la couleur
        self.ui.btn = ColorButton(self)
        # remplit la case statut de la ligne avec la liste des statuts
        self.ui.statutTableWidget.setCellWidget(num_ligne,0,item)
        # remplit la case couleur de la ligne par le bouton de choix de couleur
        self.ui.statutTableWidget.setCellWidget(num_ligne,1,self.ui.btn)      

    # Quand le champ statut a été changé par l'utilisateur dans la liste déroulante
    def changeStatut(self):
        # Met à jour la liste des statuts possibles
        self.updateListeStatut()
        # Met à jour le tableau des statuts
        self.updateStatutTable()

    # Mise à jour du tableau avec les statuts et leurs couleurs
    def updateStatutTable(self):
        # supprime toutes les lignes (en commençant par la dernière...)
        for ligne in range(self.ui.statutTableWidget.rowCount()-1, -1, -1):
            self.ui.statutTableWidget.removeRow(ligne)
        # ajoute une ligne ne position 0 grâce à la fonction addLineStatut
        self.addLineStatut(0)

    # Quand on clique sur le bouton pour ajouter une ligne dans la table des statuts
    def addStatut(self):
        if self.ui.textFileLineEdit.text() == '':
            QtGui.QMessageBox.warning(self, 'Pas de fichier en entrée', "Veuillez choisir un fichier en entrée.")
            raise IOError, "pas de fichier en entree"
        # repere l'endroit où doit être ajoutée la ligne
        row = self.ui.statutTableWidget.rowCount()
        # fait appel à la fonction addLineStatut pour insérer cette ligne
        self.addLineStatut(row)

    # Suppression de la ou les ligne(s) sélectionnée(s) dans le tableau des statuts
    def removeStatut(self):
        if self.ui.textFileLineEdit.text() == '':
            QtGui.QMessageBox.warning(self, 'Pas de fichier en entrée', "Veuillez choisir un fichier en entrée.")
            raise IOError, "pas de fichier en entree"
        # Fait une liste de tous les éléments sélectionnés
        itemSelec = self.ui.statutTableWidget.selectedIndexes()
        # Récupère seulement le numéro des lignes sélectionnées, soir le 1er tiers de itemSelec
        rowSelec = [i.row() for i in itemSelec[:len(itemSelec)/2]]
        # Ordonne la liste du plus grand au plus petit, sinon les numéros de ligne changent au fur et à mesure qu'on en supprime
        ##rowSelec.reverse()
        rowSelec.sort(reverse = True)
        # Si l'utilisateur n'a sélectionné aucune ligne
        if rowSelec == []:
            QtGui.QMessageBox.warning(self, "pas de ligne sélectionnée", "Veuillez sélectionner une ligne du tableau.")
        # Supprime chaque ligne sélectionnée
        for ligne in rowSelec:
            self.ui.statutTableWidget.removeRow(ligne)
        # Désélectionne tout
        self.ui.statutTableWidget.setCurrentCell(-1,-1)
        self.ui.statutTableWidget.clearSelection()       

    # Quand on clique sur OK
    def ok(self):
        
        #############################
        # Vérifs
        #############################

        # si aucun fichier texte choisi
        if self.ui.textFileLineEdit.text() == '':
            QtGui.QMessageBox.warning(self, 'Pas de fichier en entrée', 'Veuillez choisir un fichier en entrée.')
            raise IOError, "pas de fichier en entree"

        if (self.ui.statutTableWidget.rowCount()) == 0:
            QtGui.QMessageBox.warning(self, "pas de statut", "Merci de sélectionner au moins un statut.")
            raise IOError, "pas de statut"           


        #############################
        # Récupération des variables
        #############################
        
        # numéro de la colonne où sont les années de naissance
        num_col_annee = self.ui.anneeNaissComboBox.currentIndex() + 1
        # numéro de la colonne où sont les statuts
        num_col_statut = self.ui.statutComboBox.currentIndex() + 1
        # numéro de la colonne où est le sexe
        num_col_sexe = self.ui.sexeComboBox.currentIndex() + 1
        # liste des différents statuts possible
        statut_possible = []
        for row in range(self.ui.statutTableWidget.rowCount()):
            item = self.ui.statutTableWidget.cellWidget(row,0)
            if str(item.currentText()) in statut_possible:
                QtGui.QMessageBox.warning(self, "statut en double", "Vous avez choisi plus d'une fois le même statut!")
                raise IOError, "statut en double"
            statut_possible.append(str(item.currentText()))
        # Les mêmes, tels qu'ils apparaîtront dans la légende (pas implémenté)
        statut_legende = statut_possible
        # liste des couleurs à utiliser pour chaque statut
        liste_couleur = []
        for row in range(self.ui.statutTableWidget.rowCount()):
            item = self.ui.statutTableWidget.cellWidget(row,1)
            liste_couleur.append(str(item.palette().color(1).name()))
        # choix '-- Tous --' : on prend en compte tous les statuts
        if statut_possible == ['-- Tous --']:
            # les couleurs et les hachures sont les mêmes pour tous
            liste_couleur = liste_couleur * len(statut_possible)
        # couleur de la bordure des barres de l'histogramme
        couleur_bordure = 'white'
        # année courante
        auj = self.ui.anneeSpinBox.value()
        # taille de chaque classe d'âge
        taille_cl = self.ui.tailleClasseSpinBox.value()
        # début de la 1ère classe d'âge
        deb_cl = self.ui.debClasseSpinBox.value()
        # début de la dernière classe d'âge
        fin_cl = int(self.ui.finClasseComboBox.currentText())


        ########################
        # fonctions
        ########################
    
        # transforme une liste d'années de naissance en liste de débuts de classe d'âge
        def annee_vers_classe(liste_annee, cl, auj):
            # transforme la liste d'années de naissance en liste d'âges
            liste_cl = [auj - i for i in liste_annee]
            # transforme cette liste d'âges en liste de début de classe d'âge
            liste_cl = [i - (i-cl[1])%taille_cl for i in liste_cl]
            # remplace les valeurs inférieures à la 1ère valeur de cl
            liste_cl = [0 if i < cl[1] else i for i in liste_cl]
            # remplace les valeurs supérieures à fin_cl par fin_cl
            liste_cl = [cl[-1] if i > cl[-1] else i for i in liste_cl]
            return liste_cl

        # Remplissage de dic_statut et dic_lg en fonction de liste_ligne
        def rempl_dic(liste_ligne, dic_statut, num_col_statut, num_col_annee):
            # Remplissage de dic_statut en fonction de liste_ligne
            # Si aucun statut n'a été choisi
            if dic_statut == {'-- Tous --':[]}:
                for i in liste_ligne:
                    try:
                        dic_statut['-- Tous --'].append(int(i[num_col_annee - 1]))
                    except:
                        continue
            # Si une colonne statut a été choisie
            else:
                for i in liste_ligne:
                    try:
                        dic_statut[i[num_col_statut - 1]].append(int(i[num_col_annee - 1]))
                    except:
                        continue

        # crée une liste avec les débuts de chaque classe (type [0,25,30,35...]
        def liste_classe(deb_cl, fin_cl, taille_cl):
            cl=[0]
            i = deb_cl
            while i <= fin_cl:
                cl.append(i)
                i = i + taille_cl
            return cl

        # Crée le graph
        def creation_graphs(dic_lg, statut_possible, liste_couleur):
            # création du 1er graph
            p.append(plt.barh(position,dic_lg[statut_possible[0]],width,align='center',\
                              edgecolor =couleur_bordure,color=liste_couleur[0]))
            # num du graph en cours
            k = 1
            # liste des longueurs des graphs précédents
            liste_left = [dic_lg[statut_possible[0]]]
            for i in statut_possible[1:]:
                # liste contenant la somme des longueurs des graphs précédents
                sum_left = [sum(j) for j in zip(*liste_left)]
                # création des graphs suivant, qui s'empilent chacun sur les graphs précédents
                p.append(plt.barh(position,dic_lg[i],width,align='center',\
                                  edgecolor =couleur_bordure,color=liste_couleur[k],left=sum_left))
                # mise à jour de la liste des graphs précédents
                liste_left.append(dic_lg[i])
                # mise à jour du num du graph en cours
                k = k + 1


        ########################
        # Variables du script
        ########################

        # dictionnaire dont les clés sont les éléments de statut_possible
        # chaque valeur est une liste vide qui contiendra les débuts de classe d'âge de toutes les personnes du statut
        # ex. : {'chercheur' : [40, 35, 45, 55, 35], 'ita' : [40, 30, 60]}
        dic_statut_f = dict((i, []) for i in statut_possible)
        dic_statut_h = dict((i, []) for i in statut_possible)
        # liste des débuts de chaque classe d'âge (type [0,25,30,35...])
        cl = liste_classe(deb_cl, fin_cl, taille_cl)
        # dictionnaire dont les clés sont les statuts possibles
        # chaque valeur est une liste vide qui contiendra le nombre de personnes dans chaque classe
        # ex.  : {'Chercheur': [0, 1, 9, 7, 11, 5, 3, 2, 0], 'ITA': [0, 1, 0, 1, 0, 2, 0, 2, 0]}
        dic_lg_f = dict((i, [0] * len(cl)) for i in statut_possible)
        dic_lg_h = dict((i, [0] * len(cl)) for i in statut_possible)
        # Nombre de classes d'âge
        N = len(cl)
        # liste qui contiendra les graphs
        p = []
        # Valeur du champ sexe EN MAJUSCULES pour un homme et une femme
        sexe_homme = ['H', 'HOMME', 'M', 'MALE', 'XY']
        sexe_femme = ['F', 'FEMME', 'FEMALE', 'XX']


        ########################
        # Le script
        ########################

        # Récupère le contenu du fichier texte
        global liste_ligne
        # Crée une liste pour les femmes et une pour les hommes
        liste_ligne_f = [i for i in liste_ligne if i[num_col_sexe - 1].upper() in sexe_femme]
        liste_ligne_h = [i for i in liste_ligne if i[num_col_sexe - 1].upper() in sexe_homme]

        # Remplissage de dic_statut fonction de liste_ligne
        rempl_dic(liste_ligne_f, dic_statut_f, num_col_statut, num_col_annee)
        rempl_dic(liste_ligne_h, dic_statut_h, num_col_statut, num_col_annee)

        # Dans dic_statut, on remplace les années de naissance par l'âge
        for i in statut_possible:
            dic_statut_f[i] = annee_vers_classe(dic_statut_f[i], cl, auj)
            dic_statut_h[i] = annee_vers_classe(dic_statut_h[i], cl, auj)
            # Remplit dic_lg en fonction de dic_statut
            for k in dic_statut_f[i]:
                dic_lg_f[i][cl.index(k)] = dic_lg_f[i][cl.index(k)] + 1
            for k in dic_statut_h[i]:
                dic_lg_h[i][cl.index(k)] = dic_lg_h[i][cl.index(k)] + 1
                
        # la position des barres sur l'axe des Y
        position = range(1,N+1)
        # les étiquettes pour les classes d'âge
        labels = cl
        if taille_cl == 1:
            labels = [str(i) + ' ans' if i > 1 else str(i) + ' an' for i in labels]
        else:
            labels = [str(i) + ' - ' + str(i + taille_cl - 1) + ' ans' for i in labels]
        labels[0] = '- de ' + str(deb_cl) + ' ans' if deb_cl > 1 else '- de ' + str(deb_cl) + ' an'
        labels[-1] = str(fin_cl) + ' ans et +' if fin_cl > 1 else str(fin_cl) + ' an et +'
        # définit la largeur des barres pour qu'elles se touchent
        width = 1

        # Variable globale avec le numéro de figure, pour pouvoir en créer plusieurs
        global num_fig
        num_fig = num_fig + 1
        plt.figure(num_fig)

        # Détermine la plus grande longueur, pour pouvoir déterminer le max de l'axe des X
        lg_totales_f = [sum(i) for i in zip(*dic_lg_f.values())]
        lg_totales_h = [sum(i) for i in zip(*dic_lg_h.values())]
        max_lg = max(max(lg_totales_f), max(lg_totales_h))

        # Création du graph pour les hommes (à gauche)
        plt.subplot(1,2,1)
        creation_graphs(dic_lg_h, statut_possible, liste_couleur)
        # ajout de la légende sauf si pas besoin (pas de statut)
        if dic_statut_f.keys() != ['-- Tous --']:
            liste_patchs = [i[0] for i in p]
            plt.legend(liste_patchs, statut_legende, loc='best', frameon=False, prop={"size":15})
        # pour ne pas avoir de décimales sur l'axe des X
        plt.xticks(range(1,max_lg),range(1,max_lg))
        # Définit les min et max pour l'axe des X et des Y (xmin, xmax, ymin, ymax)
        plt.axis([0,max_lg,0.5,N+0.5])
        # inverse l'axe des X
        plt.gca().invert_xaxis()
        # pour l'axe des X, n'affiche les ticks qu'en bas
        plt.gca().get_xaxis().tick_bottom()
        # pour l'axe des Y, n'affiche pas les ticks
        for tick in plt.gca().get_yaxis().get_major_ticks():
            tick.label1On = False
            tick.tick1On = False
            tick.tick2On = False
            # pas réussi à faire fonctionner gridOn
            #tick.gridOn = False
        # Grille
        plt.gca().get_xaxis().grid(color=couleur_bordure, linestyle = '-')

        # Création du graph pour les femmes (à droite)
        plt.subplot(1,2,2)
        creation_graphs(dic_lg_f, statut_possible, liste_couleur)
        # pour avoir les étiquettes en ordonnées
        plt.yticks([i for i in position], labels)
        # pour ne pas avoir de décimales sur l'axe des X
        plt.xticks(range(1,max_lg),range(1,max_lg))
        # Définit les min et max pour l'axe des X et des Y (xmin, xmax, ymin, ymax)
        plt.axis([0,max_lg,0.5,N+0.5])
        # pour l'axe des X, n'affiche les ticks qu'en bas
        plt.gca().get_xaxis().tick_bottom()
        # pour l'axe des Y, n'affiche pas les ticks
        for tick in plt.gca().get_yaxis().get_major_ticks():
            tick.tick1On = False
            tick.tick2On = False
            # pas réussi à faire fonctionner gridOn
            #tick.gridOn = False
        plt.gca().get_xaxis().grid(color=couleur_bordure, linestyle = '-')

        # And voilà!
        plt.show()
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
