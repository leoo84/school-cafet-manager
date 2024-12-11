#!/bin/bash

# List of packages to install
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

# Check administrative rights
if [[ $EUID -ne 0 ]]; then
  echo "Ce script doit être exécuté avec les droits d'administration (sudo)."
  exit 1
fi

# Function to install packages with apt
install_with_apt() {
  echo "Détection : Système basé sur Debian (apt)"
  apt update
  apt install -y "${PACKAGES[@]}"
}

# Function to install packages with dnf
install_with_dnf() {
  echo "Détection : Système basé sur Fedora/Red Hat (dnf)"
  dnf install -y "${PACKAGES[@]}"
}

# Function to install packages with yum
install_with_yum() {
  echo "Détection : Système basé sur Red Hat/CentOS (yum)"
  yum install -y "${PACKAGES[@]}"
}

# Function to install packages with zypper
install_with_zypper() {
  echo "Détection : Système basé sur openSUSE (zypper)"
  zypper install -y "${PACKAGES[@]}"
}

# Detect package manager and install packages
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