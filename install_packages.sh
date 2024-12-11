#!/bin/bash

# Liste des packages à installer
PACKAGES=(
  build-essential
  libgirepository1.0-dev
  gcc
  libcairo2-dev
  pkg-config
  python3-dev
  gir1.2-gtk-4.0
  python3-gi
  python3-gi-cairo
  libgtk-3-dev
  python3.12-venv
)

# Vérifier les droits d'administration
if [[ $EUID -ne 0 ]]; then
  echo "Ce script doit être exécuté avec les droits d'administration (sudo)."
  exit 1
fi

# Fonction pour installer des packages avec apt
install_with_apt() {
  echo "Détection : Système basé sur Debian (apt)"
  apt update
  apt install -y "${PACKAGES[@]}"
}

# Fonction pour installer des packages avec dnf
install_with_dnf() {
  echo "Détection : Système basé sur Fedora/Red Hat (dnf)"
  dnf install -y "${PACKAGES[@]}"
}

# Fonction pour installer des packages avec yum
install_with_yum() {
  echo "Détection : Système basé sur Red Hat/CentOS (yum)"
  yum install -y "${PACKAGES[@]}"
}

# Fonction pour installer des packages avec zypper
install_with_zypper() {
  echo "Détection : Système basé sur openSUSE (zypper)"
  zypper install -y "${PACKAGES[@]}"
}

# Détecter le gestionnaire de paquets et installer les packages
if command -v apt &> /dev/null; then
  install_with_apt
elif command -v dnf &> /dev/null; then
  install_with_dnf
elif command -v yum &> /dev/null; then
  install_with_yum
elif command -v zypper &> /dev/null; then
  install_with_zypper
else
  echo "Aucun gestionnaire de paquets compatible n'a été détecté."
  exit 1
fi

echo "Installation terminée."