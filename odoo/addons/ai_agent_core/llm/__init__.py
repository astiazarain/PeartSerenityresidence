# -*- coding: utf-8 -*-
"""Piezas sin modelo Odoo de la capa de proveedores de IA.

Viven fuera de models/ porque no son modelos: son funciones puras
(clasificación de errores, backoff, lectura de uso y de catálogos, cifrado)
que se prueban con cuerpos reales de cada API sin levantar un proveedor.
"""
