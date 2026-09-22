# Peart Serenity - Expediente clínico (`peart_clinical_record`)

Expediente del residente, historia clínica, registro diario por turno, hoja de
medicación (MAR), incidentes y acceso de la familia desde el sitio web.
Depende de `peart_serenity` y `ai_agent_core` (ARIA). Odoo 19.

## Roles

| Rol | Puede |
|---|---|
| **Médico** | Todo lo clínico: diagnósticos, recetas, ingreso, valoraciones, escalas. |
| **Enfermera** | Registro de turno, medicación (dar/rechazar/omitir), incidentes, alergias, plan de cuidados, valoraciones. Ve diagnósticos y recetas en solo lectura. |
| **Administrador** | Altas, vínculos familiares, consentimientos, contactos y documentos no clínicos (ID, legales, seguro, facturación). **Sin acceso a datos clínicos.** |
| **CEO** | Solo lectura de todo, más el registro de accesos. |
| **Familia** (portal) | Solo lo que el personal marcó como visible, de sus residentes vinculados, por el sitio web. Sin acceso directo a Odoo. |

Se asignan en *Ajustes → Usuarios → Peart Clinical Record*. Un usuario tiene un rol clínico a la vez.

## Flujo del día a día

1. **Ingreso:** al marcar una admisión como *Admitted* se crea el residente. Complete el *Ingreso clínico*.
2. **Turno (Día 07-19 / Noche 19-07):** *Residents → Shift Log* crea el registro de cada residente en residencia. Se llena en la lista y se **cierra**; un registro cerrado solo admite addenda.
3. **Medicación:** el médico receta en la ficha; las dosis se programan solas (tarea diaria + al crear la orden). En *Medication Round* la enfermera marca cada dosis. Rechazada, omitida o retenida exigen motivo.
4. **Incidentes:** los graves avisan a los médicos. No se cierran sin registrar que se avisó al médico y a la familia.
5. **Informes PDF:** en la ficha del residente, *Imprimir → Resident Record*. En *Daily Logs*, seleccione registros → *Shift Summary*. Cada impresión queda auditada.

## Dar acceso a una familia

1. La familia crea su cuenta en el sitio web (portal).
2. En la ficha del residente → **Consents**: registre *Family access to the record* (y *AI assistant (ARIA)* si aceptó ARIA), con el documento firmado.
3. **Family Access**: agregue su usuario y marque *Access Enabled*. Sin consentimiento vigente, Odoo no deja habilitarlo; al revocar el consentimiento se corta el acceso.
4. Marque qué se comparte: cada diagnóstico, medicación, plan, documento, valoración e incidente tiene *Visible to family*. Los registros de turno cerrados se comparten salvo que se desmarque; las **notas internas nunca** se comparten.
5. La familia entra en `/family`.

## ARIA para familias

*Ajustes → Peart Clinical Record → AI provider for families.* **Es obligatorio elegir uno**: no hay proveedor por defecto ni respaldo, porque los datos del residente se envían a ese proveedor. Elija uno aprobado para datos de salud. ARIA solo ve lo que la familia ya puede ver, no da consejo médico y pasa a enfermería (tarea en Odoo) lo clínico o urgente.

## Auditoría

*Residents → Family Portal Activity* (CEO y Administrador): cada consulta, descarga y pregunta a ARIA de la familia, cada apertura de expediente por el personal (1 por 10 min) y cada informe impreso.

## Antes de usarlo con residentes reales

- [ ] **Validación clínica** por su médico o directora de enfermería: escalas y puntos de corte (Barthel, Katz, Morse, Norton, SPMSQ, GDS-15) y los **rangos de alerta de signos vitales** (`models/peart_daily_log.py`, `VITAL_LIMITS`).
- [ ] **Legal:** registro del negocio ante el Ministerio de Salud (Nursing Homes Registration Act), registro ante la OIC y responsable de protección de datos (Data Protection Act 2020); revisar el texto de consentimiento y la Política de Privacidad (incluye el envío de datos al proveedor de IA).
- [ ] **Producción:** HTTPS, copias de seguridad cifradas de la base de datos y de los adjuntos, `web.base.url` correcto.
- [ ] **nginx:** la ruta `/family` debe llegar a la app web (ya está en `infra/nginx/default.conf`; replicar en producción).
- [ ] **PDF:** `web.base.url` (o `report.url`) debe ser alcanzable desde el servidor de Odoo, o los PDF salen sin estilo. En Docker local: `report.url = http://localhost:8069`.
- [ ] Probar una familia de punta a punta con datos de demostración antes del primer residente real.

## Límites conocidos

- Las alertas de signos vitales (`Alert Flags`) se guardan en inglés al cerrar el turno.
- El texto libre que escribe el personal no se traduce.
- No hay MNA-SF (licencia) ni Mini-Cog (permiso); se usa SPMSQ.
- Con más de una base de datos en el mismo servidor Odoo, las páginas públicas y los PDF pueden fallar: en desarrollo, borre las bases de prueba.

## Pruebas

```
docker exec peartserenity odoo -d <base_de_prueba> -i peart_clinical_record \
  --test-tags /peart_clinical_record --stop-after-init --http-port=8099 --gevent-port=8098
```
Use siempre una base desechable, no la real.
