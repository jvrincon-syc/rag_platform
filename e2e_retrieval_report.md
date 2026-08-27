# Reporte end-to-end plataforma RAG (local, BGE-M3)

- Generado: 2026-08-25T23:23:03.058699+00:00
- Proyecto: `proj_sst-general`
- Variante: `ragv_local-bge`
- Release: `ragr_f06f581e6ad946df`
- Build attempt: 1
- Documentos: 55
- Vectores release-scoped: 353

## Pipeline

- chunk bundles: 55
- embedding bundles: 55
- indexing materializations: 55
- indexing nodes: 606
- embedding/indexing run release ids: `['ragr_f06f581e6ad946df']`

## Embedding recipe

- provider: `bge`
- model: `BAAI/bge-m3`
- dimension: 1024
- metric: `cosine`
- normalization: `l2`
- profile: `local-bge-m3-v1`

## Retrieval - 53 preguntas, top_k=8

### Que establece la politica de seguridad y salud en el trabajo?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6661 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | \| "POLÍTICA DE SEGURIDAD Y SALUD EN'EL'TRABAJO - j |
| 2 | 0.6653 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 3 | 0.6575 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 4 | 0.6332 | general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 5 | 0.6305 | general_sst/manuales/politica/politica.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 6 | 0.6301 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | l l Proteger: la seguridad y: salud «de todos los trabajadores, mediante la mejora continua del Sistema de Gestión de la Seguridad y Salud en el Trabajo. Destinar los recursos financieros, humanos, técnicos, físicos y la |
| 7 | 0.6241 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 8 | 0.6223 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |

### Cuales son los objetivos del SG-SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5858 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 2 | 0.5833 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 3 | 0.5721 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 4 | 0.5584 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.5229 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 6 | 0.5076 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |
| 7 | 0.4917 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 8 | 0.4892 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |

### Como identifica la empresa los peligros y valora los riesgos?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6261 | general_sst/manuales/planificacion/planificacion_info.md | child |  | La metodologia de identificacion de peligros y valoracion de riesgos, permite la participacion activa de los trabajadores, partes interesadas y la priorizacion de los riesgos para establecer medidas de intervencion con e |
| 2 | 0.6180 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | GESTION DEL CAMBIO  La empresa evaluara el impacto sobre la seguridad y salud, que puedan generar los cambios internos (introduccion de nuevos procesos, cambios en los metodos de trabajo, adquisiciones, instalaciones, en |
| 3 | 0.5969 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | CONTROL DE PROVEEDORES Y CONTRATISTAS  La empresa cuenta con un procedimiento para la seleccion y evaluacion de proveedores que tiene lineamientos y requisitos en seguridad y salud en el trabajo. A continuacion se detall |
| 4 | 0.5799 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 5 | 0.5736 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 6 | 0.5603 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 63. Todas las empresas y las entidades administradoras de riesgos profesionales  deberán llevar estadísticas de los accidentes de trabajo y de las enfermedades profesionales, para lo cual deberán, en cada caso,  |
| 7 | 0.5503 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 8 | 0.5403 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 60. Los trabajadores deberán someterse a todas las medidas de higiene y seguridad  industrial que prescriben las autoridades del ramo en general y en particular a las que ordene la empresa para prevención de los |

### Que programas conforman la planificacion del SG-SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5834 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 2 | 0.5713 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 3 | 0.5578 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 4 | 0.5408 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 5 | 0.5229 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 6 | 0.5125 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 7 | 0.5113 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 8 | 0.4965 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |

### Como se gestionan los requisitos legales en SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5919 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 2 | 0.5804 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 3 | 0.5623 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 4 | 0.5517 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 5 | 0.5276 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 6 | 0.5205 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 7 | 0.5185 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 98. Seguridad y salud en el trabajo. En todas las modalidades a distancia se aplicarán  las obligaciones del SG-SST y la gestión de riesgos en los domicilios o lugares habilitados, con apoyo de la ARL. (Decreto  |
| 8 | 0.5030 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |

### Que contempla la gestion del cambio en seguridad y salud?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6613 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | GESTION DEL CAMBIO  La empresa evaluara el impacto sobre la seguridad y salud, que puedan generar los cambios internos (introduccion de nuevos procesos, cambios en los metodos de trabajo, adquisiciones, instalaciones, en |
| 2 | 0.5571 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 3 | 0.5478 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 4 | 0.5377 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | l l Proteger: la seguridad y: salud «de todos los trabajadores, mediante la mejora continua del Sistema de Gestión de la Seguridad y Salud en el Trabajo. Destinar los recursos financieros, humanos, técnicos, físicos y la |
| 5 | 0.5252 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 6 | 0.5242 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 7 | 0.5089 | general_sst/manuales/planificacion/planificacion_info.md | child |  | La metodologia de identificacion de peligros y valoracion de riesgos, permite la participacion activa de los trabajadores, partes interesadas y la priorizacion de los riesgos para establecer medidas de intervencion con e |
| 8 | 0.5009 | general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |

### Como se prepara la empresa para emergencias?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6537 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | GESTION DEL CAMBIO  La empresa evaluara el impacto sobre la seguridad y salud, que puedan generar los cambios internos (introduccion de nuevos procesos, cambios en los metodos de trabajo, adquisiciones, instalaciones, en |
| 2 | 0.5656 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | CONTROL DE PROVEEDORES Y CONTRATISTAS  La empresa cuenta con un procedimiento para la seleccion y evaluacion de proveedores que tiene lineamientos y requisitos en seguridad y salud en el trabajo. A continuacion se detall |
| 3 | 0.5341 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | cualquier error, daño, falla o accidente que ocurran a máquinas, procesos, instalaciones, materiales o personas.  21. Comunicar accidentes de trabajo por leves que sean, en forma inmediata a la empresa. 22. Guardar compl |
| 4 | 0.5340 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 70. Son obligaciones especiales de la empresa:  1. Poner a disposición de los trabajadores, salvo estipulación en contrario, los instrumentos adecuados y las materias primas necesarias para la realización de las |
| 5 | 0.5309 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 45. Para la concurrencia al servicio médico correspondiente, la oportunidad del aviso a  la empresa debe ser anterior al hecho que lo constituye, es decir, con una anticipación mínima de dos (2) días o según lo  |
| 6 | 0.5143 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Solicitar periodicamente a la empresa informes sobre accidentalidad y enfermedades laborales. Servir como organismo de coordinacion entre empleador y los trabajadores en la solucion de los problemas relativos a la seguri |
| 7 | 0.5072 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | 13. Reconocer el pago de los instrumentos y útiles de trabajo que por su indebida, negligente e  irresponsable utilización sean averiados y/o destruidos.  14. Observar estrictamente lo establecido o lo que establezca La  |
| 8 | 0.5051 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 44. La empresa concederá a sus trabajadores los permisos necesarios para el ejercicio  del derecho al sufragio y para el desempeño de cargos oficiales transitorios de forzosa aceptación, en caso de grave calamid |

### Que lineamientos aplican a proveedores y contratistas en SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5615 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 2 | 0.5510 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | CONTROL DE PROVEEDORES Y CONTRATISTAS  La empresa cuenta con un procedimiento para la seleccion y evaluacion de proveedores que tiene lineamientos y requisitos en seguridad y salud en el trabajo. A continuacion se detall |
| 3 | 0.5175 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 4 | 0.5091 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 5 | 0.5043 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 6 | 0.4923 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 7 | 0.4843 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |
| 8 | 0.4727 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 98. Seguridad y salud en el trabajo. En todas las modalidades a distancia se aplicarán  las obligaciones del SG-SST y la gestión de riesgos en los domicilios o lugares habilitados, con apoyo de la ARL. (Decreto  |

### Como se hacen auditorias internas del SG-SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7297 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 2 | 0.6135 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 3 | 0.5907 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |
| 4 | 0.5799 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.5723 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 6 | 0.5545 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 7 | 0.5449 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 8 | 0.5306 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |

### Como se revisa el SG-SST por la alta direccion?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6011 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 2 | 0.5669 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 3 | 0.5511 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |
| 4 | 0.5508 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.5455 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 6 | 0.5094 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 7 | 0.4976 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 8 | 0.4945 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | SA ALS ls LL DIAPADIFY Lo. EN'EL'TRABAJO - ] " Vero os \| \| _ TRABAJO \| o  AAA cg SR A y IT + . x= . y > Sistemes y Computadores S.A. PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO - POLÍTICA DE SEGURIDAD Y |

### Que fuentes se usan para identificar oportunidades de mejora continua?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5927 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 2 | 0.4652 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 3 | 0.4447 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 4 | 0.4401 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | GESTION DEL CAMBIO  La empresa evaluara el impacto sobre la seguridad y salud, que puedan generar los cambios internos (introduccion de nuevos procesos, cambios en los metodos de trabajo, adquisiciones, instalaciones, en |
| 5 | 0.4376 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 6 | 0.4369 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1.2 A nivel de canales de comunicación  La Compañía dispone de canales de comunicación como la intranet corporativa, correos electrónicos, pantallas digitales, con el fin de: • Permitir a los colaboradores expresar ide |
| 7 | 0.4358 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Conductas asociadas:  • Reconocer los logros y buenos resultados de los servidores, no apropiarse de los logros que no correspondan.  • Delegar en los colaboradores funciones, como forma de faci |
| 8 | 0.4356 | convivencia_laboral/manual/normas_convivencia.md | child |  | 8. Valorar el buen trabajo y fomentar el reconocimiento de logros sincero y oportuno entre companeros.  Conductas asociadas:  • Reconocer los logros y buenos resultados de los servidores, no apropiarse de los logros que  |

### Como se gestionan las acciones correctivas y preventivas?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6907 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 2 | 0.5845 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1 Funciones preventivas  - Recibir y tramitar quejas: Atender las denuncias relacionadas con presunto acoso laboral y otros comportamientos que afecten la convivencia laboral.  - Escuchar a las partes involucradas: Bri |
| 3 | 0.5780 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1  Funciones preventivas  - Recibir y tramitar quejas: Atender las denuncias relacionadas con presunto acoso laboral y otros comportamientos que afecten la convivencia laboral. - Escuchar a las partes involucradas: Bri |
| 4 | 0.5706 | general_sst/manuales/aplicacion/aplicacion_info.md | child |  | GESTION DEL CAMBIO  La empresa evaluara el impacto sobre la seguridad y salud, que puedan generar los cambios internos (introduccion de nuevos procesos, cambios en los metodos de trabajo, adquisiciones, instalaciones, en |
| 5 | 0.5699 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 90. Medidas preventivas y correctivas del acoso laboral y sexual: La empresa proveerá  de mecanismos de prevención de las conductas de acoso laboral, sexual y de diversidad de género, estableciendo un procedimie |
| 6 | 0.5393 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 7 | 0.5341 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 100. Ruta de prevención y atención. Además de lo previsto en la Ley 1010 de 2006, la  empresa implementará una **ruta específica** para la prevención, atención y protección frente al **acoso sexual**: canales co |
| 8 | 0.5267 | general_sst/manuales/planificacion/planificacion_info.md | child |  | La metodologia de identificacion de peligros y valoracion de riesgos, permite la participacion activa de los trabajadores, partes interesadas y la priorizacion de los riesgos para establecer medidas de intervencion con e |

### Como se investigan incidentes accidentes y enfermedades laborales?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7338 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 2 | 0.6301 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 63. Todas las empresas y las entidades administradoras de riesgos profesionales  deberán llevar estadísticas de los accidentes de trabajo y de las enfermedades profesionales, para lo cual deberán, en cada caso,  |
| 3 | 0.6062 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 62. Es obligación del empleador de acuerdo con la Resolución 1401 de 2007 realizar  investigaciones de todos los accidentes de trabajo como objetivo principal, prevenir la ocurrencia de nuevos eventos, lo cual c |
| 4 | 0.6009 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 64. Todo accidente de trabajo o enfermedad profesional que ocurra en una empresa o  actividad económica deberá ser informado por el empleador a la entidad administradora de riesgos laborales y a la entidad promo |
| 5 | 0.5774 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Solicitar periodicamente a la empresa informes sobre accidentalidad y enfermedades laborales. Servir como organismo de coordinacion entre empleador y los trabajadores en la solucion de los problemas relativos a la seguri |
| 6 | 0.5669 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Proponer a la administracion de la empresa o establecimiento de trabajo la adopcion de medidas y el desarrollo de actividades que procuren y mantengan la salud en los lugares y ambientes de trabajo. Proponer y participar |
| 7 | 0.5592 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 61. En caso de accidente no mortal, aún el más leve o de apariencia insignificante el  trabajador deberá comunicar inmediatamente al empleador, a su representante, o a quien haga sus veces para que se provea la  |
| 8 | 0.5462 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |

### Que debe comunicarse al COPASST sobre investigaciones de accidentes?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6534 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 2 | 0.6234 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 3 | 0.5223 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 61. En caso de accidente no mortal, aún el más leve o de apariencia insignificante el  trabajador deberá comunicar inmediatamente al empleador, a su representante, o a quien haga sus veces para que se provea la  |
| 4 | 0.5212 | copasst/comunicacion.md | child |  | Escribir al correo: copasst@syc.com.co Seguridadysalud@syc.com.co Llamadas y WhatsApp: 3176451139 |
| 5 | 0.5165 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 6 | 0.5135 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 7 | 0.4974 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 62. Es obligación del empleador de acuerdo con la Resolución 1401 de 2007 realizar  investigaciones de todos los accidentes de trabajo como objetivo principal, prevenir la ocurrencia de nuevos eventos, lo cual c |
| 8 | 0.4946 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |

### Que responsabilidades tiene la ARL en seguridad y salud en el trabajo?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6275 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 98. Seguridad y salud en el trabajo. En todas las modalidades a distancia se aplicarán  las obligaciones del SG-SST y la gestión de riesgos en los domicilios o lugares habilitados, con apoyo de la ARL. (Decreto  |
| 2 | 0.5304 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | l l Proteger: la seguridad y: salud «de todos los trabajadores, mediante la mejora continua del Sistema de Gestión de la Seguridad y Salud en el Trabajo. Destinar los recursos financieros, humanos, técnicos, físicos y la |
| 3 | 0.5052 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 4 | 0.5036 | general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md | child |  | Solicitar periodicamente a la empresa informes sobre accidentalidad y enfermedades laborales. Servir como organismo de coordinacion entre empleador y los trabajadores en la solucion de los problemas relativos a la seguri |
| 5 | 0.5015 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 58. Es obligación del empleador velar por la salud, seguridad e higiene de los trabajadores a su cargo en su ambiente o contexto laboral. Igualmente, es su obligación garantizar los recursos necesarios para impl |
| 6 | 0.4958 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 60. Los trabajadores deberán someterse a todas las medidas de higiene y seguridad  industrial que prescriben las autoridades del ramo en general y en particular a las que ordene la empresa para prevención de los |
| 7 | 0.4949 | convivencia_laboral/manual/marco_legal.md | child |  | · Resolucion 652 de 2012: “por la cual se establece la conformacion y funcionamiento del Comite de Convivencia Laboral en entidades publicas y empresas privadas y se dictan otras disposiciones.” Modificada por la Resoluc |
| 8 | 0.4912 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | SA ALS ls LL DIAPADIFY Lo. EN'EL'TRABAJO - ] " Vero os \| \| _ TRABAJO \| o  AAA cg SR A y IT + . x= . y > Sistemes y Computadores S.A. PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO - POLÍTICA DE SEGURIDAD Y |

### Que responsabilidades de SST tiene la organizacion?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6108 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 2 | 0.5827 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 3 | 0.5781 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 4 | 0.5464 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.5284 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 98. Seguridad y salud en el trabajo. En todas las modalidades a distancia se aplicarán  las obligaciones del SG-SST y la gestión de riesgos en los domicilios o lugares habilitados, con apoyo de la ARL. (Decreto  |
| 6 | 0.5273 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 7 | 0.5181 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 8 | 0.5159 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |

### Como funciona la induccion y capacitacion anual en SST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6152 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |
| 2 | 0.5648 | general_sst/manuales/auditoria/auditoria_info.md | child |  | AUDITORIA INTERNA Para determinar la eficacia del Sistema de Gestion de Seguridad y Salud en el Trabajo, se realizaran auditorias al Sistema, para esto se cuenta con un procedimiento documentado denominado PR MC- 03 AUDI |
| 3 | 0.5462 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |
| 4 | 0.5456 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.5000 | general_sst/manuales/verificacion/verificacion_info.md | child |  | SUPERVISION Y MEDICION DE LOS RESULTADOS Se establecen los indicadores mediante los cuales se evalua la estructura, el proceso y los resultados del Sistema de Gestion de la Seguridad y Salud en el Trabajo SG-SST y se hac |
| 6 | 0.4813 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 7 | 0.4771 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 8 | 0.4720 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |

### Cuales son las funciones del COPASST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6535 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 2 | 0.6336 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 3 | 0.6304 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 4 | 0.5409 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 5 | 0.4686 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |
| 6 | 0.4649 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |
| 7 | 0.4338 | general_sst/manuales/mejora/mejora_info.md | child |  | Las recomendaciones presentadas por los trabajadores y el COPASST f. Los resultados de los programas de medicina preventiva, higiene y seguridad industrial g. El resultado de la evaluacion realizado por la alta direccion |
| 8 | 0.4330 | general_sst/manuales/mejora/mejora_info.md | child |  | SISTEMAS Y COMPUTADORES S.A, es consciente de la importancia y beneficios que trae el contar con un SG-SST, razon por la cual cada colaborador sabe la importancia de mejorar cada una de sus actividades del dia a dia, con |

### Que funciones tiene el presidente del COPASST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7093 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 2 | 0.6451 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 3 | 0.5971 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 4 | 0.5229 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |
| 5 | 0.5082 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 6 | 0.4784 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 3.2 Funciones del presidente  • Convocar a los miembros del comité a las sesiones ordinarias y extraordinarias. • Presidir y orientar las reuniones ordinarias y extraordinarias en forma dinámica y eficaz. • Tramitar ante |
| 7 | 0.4661 | convivencia_laboral/reglamento_comite/funcionamiento_comite.md | child |  | 3.2 Funciones del presidente  - Convocar a los miembros del comite a las sesiones ordinarias y extraordinarias.  - Presidir y orientar las reuniones ordinarias y extraordinarias en forma dinamica y eficaz.  - Tramitar an |
| 8 | 0.4345 | general_sst/manuales/verificacion/verificacion_info.md | child |  | Deficiencias en seguridad y salud y otras fallas en la gestion de la SST en la empresa. e. La efectividad de los programas de rehabilitacion y recuperacion de la salud de los trabajadores.  INVESTIGACION DE INCIDENTES, A |

### Que funciones tiene la secretaria del COPASST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7776 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 2 | 0.6229 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 3 | 0.6031 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 4 | 0.5202 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |
| 5 | 0.5133 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 6 | 0.4735 | convivencia_laboral/reglamento_comite/funcionamiento_comite.md | child |  | 3.3 Funciones del secretario  - Recibir y dar tramites a las quejas presentadas por escrito en las que se describa las situaciones que puedan constituir acoso laboral, asi como las pruebas que las soportan.  - Enviar por |
| 7 | 0.4703 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 3.3 Funciones del secretario  • Recibir y dar trámites a las quejas presentadas por escrito en las que se describa las situaciones que puedan constituir acoso laboral, así como las pruebas que las soportan. • Enviar por  |
| 8 | 0.4670 | general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |

### Como se puede comunicar un trabajador con el COPASST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7177 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 2 | 0.6430 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 3 | 0.5994 | copasst/comunicacion.md | child |  | Escribir al correo: copasst@syc.com.co Seguridadysalud@syc.com.co Llamadas y WhatsApp: 3176451139 |
| 4 | 0.5943 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 5 | 0.5732 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 6 | 0.5596 | general_sst/manuales/politica/politica.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 7 | 0.5590 | general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 8 | 0.5574 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |

### Quienes son los miembros principales y suplentes del COPASST 2025 a 2027?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5827 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |
| 2 | 0.5016 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 3 | 0.4849 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 4 | 0.4704 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 5 | 0.4199 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 6 | 0.3643 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 2.1 Miembros del Comité de Convivencia Laboral  2.1.1 Designación  - Si la empresa tiene menos de 5 trabajadores: El Comité estará compuesto por 1 representante del empleador y 1 representante de los trabajadores.  - Si  |
| 7 | 0.3572 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 2.1.1.1 Representantes de los colaboradores.  2 |
| 8 | 0.3503 | copasst/comunicacion.md | child |  | Escribir al correo: copasst@syc.com.co Seguridadysalud@syc.com.co Llamadas y WhatsApp: 3176451139 |

### Quien fue nombrado presidente y secretaria del COPASST?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5840 | copasst/funciones_secretario_copasst.md | child |  | 🗂️ Funciones de la Secretaria del COPASST  La Secretaria del COPASST es designada por los miembros del comite y cumple un rol organizativo y de apoyo clave para la gestion documental y el seguimiento de actividades.  Sus |
| 2 | 0.5613 | copasst/funciones_presidente_copasst.md | child |  | El presidente del Comite Paritario de Seguridad y Salud en el Trabajo (COPASST) es designado por el empleador y tiene las siguientes funciones principales:  1 -Representar al empleador dentro del comite. 2 -Convocar y pr |
| 3 | 0.5253 | copasst/miembros_copasst_2025_2027.md | child |  | REPRESENTANTES DE LOS TRABAJADORES  Miembros Principales:  1 Juan Camilo Palacios Pedraza - Colpensiones - Bogota 2 Leidy Salamanca Manrique -Evas -Floridablanca​ 3 Angie Daniela Cardenas Alvarado -Captura -Floridablanca |
| 4 | 0.5021 | copasst/funciones_copasst.md | child |  | El Decreto 1072 de 2015 establece nuevas funciones del COPASST al compilar del Decreto 1443 de 2014.  Estas son:  Recibir por parte de la alta direccion la comunicacion de la politica de seguridad y salud en el trabajo ( |
| 5 | 0.4368 | general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md | child |  | Se cuenta con un Comite Paritario de Seguridad y salud en el trabajo (COPASST), dando cumplimiento a la resolucion 2013 de 1986 y el Decreto 1295 de 1994.  El comite paritario desarrolla actividades en seguridad y salud  |
| 6 | 0.4148 | general_sst/manuales/politica/politica.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 7 | 0.4148 | general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md | child |  | La alta direccion con la participacion del COPASST ha definido la politica de Seguridad y Salud en el Trabajo, la cual es comunicada y divulgada a traves de procesos de induccion, re induccion y por medios publicitario e |
| 8 | 0.3874 | copasst/comunicacion.md | child |  | Escribir al correo: copasst@syc.com.co Seguridadysalud@syc.com.co Llamadas y WhatsApp: 3176451139 |

### Que es el comite de convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7069 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6846 | convivencia_laboral/reglamento_comite/objetivo_comite.md | child |  | El Comite de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demas reglamentos de SYC, a la prevencion y solucion de las situaciones causadas por conductas de acoso l |
| 3 | 0.6560 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 4 | 0.6450 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 5 | 0.6345 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 6 | 0.6250 | convivencia_laboral/reglamento_comite/conformacion_comite.md | child |  | 2.1 Miembros del Comite de Convivencia Laboral  2.1.1 Designacion  - Si la empresa tiene menos de 5 trabajadores: El Comite estara compuesto por 1 representante del empleador y 1 representante de los trabajadores.  - Si  |
| 7 | 0.6208 | general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md | child |  | Recibir y dar tramite a las quejas presentadas referentes a acoso laboral. Examinar de manera confidencial los casos especificos o puntuales en los que se formule queja o reclamo, que pudieran tipificar conductas o circu |
| 8 | 0.5969 | convivencia_laboral/reglamento_comite/metodologia_sesiones_comite.md | child |  | 4.2 Validez de las Reuniones  El Comite de Convivencia Laboral podra sesionar validamente con la asistencia de la mitad mas uno (1⁄2 + 1) de sus integrantes, garantizando en todo caso la representacion de ambas partes: e |

### Cuales son las funciones del comite de convivencia?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6804 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6057 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 3 | 0.6000 | convivencia_laboral/reglamento_comite/objetivo_comite.md | child |  | El Comite de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demas reglamentos de SYC, a la prevencion y solucion de las situaciones causadas por conductas de acoso l |
| 4 | 0.5968 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 5 | 0.5698 | general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md | child |  | Recibir y dar tramite a las quejas presentadas referentes a acoso laboral. Examinar de manera confidencial los casos especificos o puntuales en los que se formule queja o reclamo, que pudieran tipificar conductas o circu |
| 6 | 0.5663 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 7 | 0.5565 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1.3 A nivel de evaluacion del clima laboral, el Comite podra proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Tramite de las quejas por etapas  Primera etapa: Recepcion de la queja  El Comite  |
| 8 | 0.5403 | convivencia_laboral/reglamento_comite/metodologia_sesiones_comite.md | child |  | 4.2 Validez de las Reuniones  El Comite de Convivencia Laboral podra sesionar validamente con la asistencia de la mitad mas uno (1⁄2 + 1) de sus integrantes, garantizando en todo caso la representacion de ambas partes: e |

### Cual es el objetivo del reglamento del comite de convivencia?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6564 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6450 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 3 | 0.6266 | convivencia_laboral/reglamento_comite/objetivo_comite.md | child |  | El Comite de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demas reglamentos de SYC, a la prevencion y solucion de las situaciones causadas por conductas de acoso l |
| 4 | 0.6026 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 5 | 0.5936 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 6 | 0.5782 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  REGLAMENTO COMITÉ DE CONVIVENCIA LABORAL  1. CAPÍTULO PRIMERO: OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL.  2  2. CAPÍTULO SEGUNDO: CONFORMACIÓN DEL COMITÉ DE CONVIVENCIA LABORAL  2 |
| 7 | 0.5652 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 8 | 0.5575 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Adelantar reuniones con el fin de crear espacios de dialogo entre las partes involucradas, promoviendo compromisos mutuos para llegar a una solución efectiva de los conflictos.  OBJETIVOS ESPECÍFICOS:  • Promover un ambi |

### Como se conforma el comite de convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7209 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6808 | convivencia_laboral/reglamento_comite/conformacion_comite.md | child |  | 2.1 Miembros del Comite de Convivencia Laboral  2.1.1 Designacion  - Si la empresa tiene menos de 5 trabajadores: El Comite estara compuesto por 1 representante del empleador y 1 representante de los trabajadores.  - Si  |
| 3 | 0.6681 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 4 | 0.6515 | convivencia_laboral/reglamento_comite/objetivo_comite.md | child |  | El Comite de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demas reglamentos de SYC, a la prevencion y solucion de las situaciones causadas por conductas de acoso l |
| 5 | 0.6501 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 2.1 Miembros del Comité de Convivencia Laboral  2.1.1 Designación  - Si la empresa tiene menos de 5 trabajadores: El Comité estará compuesto por 1 representante del empleador y 1 representante de los trabajadores.  - Si  |
| 6 | 0.6455 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 7 | 0.6451 | convivencia_laboral/reglamento_comite/metodologia_sesiones_comite.md | child |  | 4.2 Validez de las Reuniones  El Comite de Convivencia Laboral podra sesionar validamente con la asistencia de la mitad mas uno (1⁄2 + 1) de sus integrantes, garantizando en todo caso la representacion de ambas partes: e |
| 8 | 0.6323 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |

### Como funcionan las reuniones del comite de convivencia?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6920 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6051 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1.3 A nivel de evaluacion del clima laboral, el Comite podra proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Tramite de las quejas por etapas  Primera etapa: Recepcion de la queja  El Comite  |
| 3 | 0.5985 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Dicho programa se pondrá en marcha en caso de evidenciarse acoso laboral por parte del comité de convivencia laboral. El programa se estructura en cuatro (4) fases:  1. Primera Fase: Valoración: Entre las partes a saber, |
| 4 | 0.5939 | convivencia_laboral/reglamento_comite/metodologia_sesiones_comite.md | child |  | 4.2 Validez de las Reuniones  El Comite de Convivencia Laboral podra sesionar validamente con la asistencia de la mitad mas uno (1⁄2 + 1) de sus integrantes, garantizando en todo caso la representacion de ambas partes: e |
| 5 | 0.5916 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 6 | 0.5895 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 7 | 0.5849 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 8 | 0.5790 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1.3 A nivel de evaluación del clima laboral, el Comité podrá proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Trámite de las quejas por etapas  Primera etapa: Recepción de la queja  El Comité  |

### Que metodologia siguen las sesiones del comite de convivencia?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6154 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.5646 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1.3 A nivel de evaluacion del clima laboral, el Comite podra proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Tramite de las quejas por etapas  Primera etapa: Recepcion de la queja  El Comite  |
| 3 | 0.5523 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1.3 A nivel de evaluación del clima laboral, el Comité podrá proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Trámite de las quejas por etapas  Primera etapa: Recepción de la queja  El Comité  |
| 4 | 0.5454 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Dicho programa se pondrá en marcha en caso de evidenciarse acoso laboral por parte del comité de convivencia laboral. El programa se estructura en cuatro (4) fases:  1. Primera Fase: Valoración: Entre las partes a saber, |
| 5 | 0.5375 | convivencia_laboral/manual/normas_convivencia.md | child |  | 9. Hacer uso adecuado y respetuoso de las zonas comunes y puestos de trabajo, garantizando que permanezcan limpios y ordenados.  Conductas asociadas:  • Respetar el espacio de trabajo compartido.  • Evitar interrumpir la |
| 6 | 0.5331 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 7 | 0.5323 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 8 | 0.5228 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |

### Como se presentan quejas o denuncias de convivencia?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6295 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1.3 A nivel de evaluacion del clima laboral, el Comite podra proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Tramite de las quejas por etapas  Primera etapa: Recepcion de la queja  El Comite  |
| 2 | 0.6217 | convivencia_laboral/manual/quejas_denuncias.md | child |  | Evidencia (opcional): Adjunta correos, mensajes, testimonios, grabaciones o cualquier soporte que ayude a sustentar la denuncia.  Llenado del formato de reporte:  Descargar el formato especifico de queja o denuncia por a |
| 3 | 0.6190 | convivencia_laboral/manual/quejas_denuncias.md | child |  | En caso de considerar que esta siendo victima de acoso, conforme a lo establecido en la Ley 1010, se solicita diligenciar el formato correspondiente y remitirlo al correo electronico convivencia@syc.com.co.  Esta queja s |
| 4 | 0.6180 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1.3 A nivel de evaluación del clima laboral, el Comité podrá proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Trámite de las quejas por etapas  Primera etapa: Recepción de la queja  El Comité  |
| 5 | 0.5943 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Dicho programa se pondrá en marcha en caso de evidenciarse acoso laboral por parte del comité de convivencia laboral. El programa se estructura en cuatro (4) fases:  1. Primera Fase: Valoración: Entre las partes a saber, |
| 6 | 0.5899 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  6. Derecho a ser escuchado por el comité de convivencia cuando identifique conductas que atenten contra la convivencia laboral de la empresa. (Incluyendo maltrato laboral o conductas de acoso).  |
| 7 | 0.5867 | general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md | child |  | Recibir y dar tramite a las quejas presentadas referentes a acoso laboral. Examinar de manera confidencial los casos especificos o puntuales en los que se formule queja o reclamo, que pudieran tipificar conductas o circu |
| 8 | 0.5852 | convivencia_laboral/manual/1761580555950_syc_RE.RH-04SST23102025.pdf | child |  | FORMATO PARA INTERPONER QUEJA POR PRESUNTO ACOSO ANTE EL COMITÉ DE CONVIVENCIA. RE.RH-04 NIVEL DE USO INTERNO CÓDIGO Versión |

### A que correo se envian las quejas de convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6560 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | - Garantizar los mecanismos y medios para que los trabajadores, puedan  presentar queja frente a la' posible vulneración de este derecho. Tener en cuenta que los horarios laborales están definidos de acuerdo al proyecto  |
| 2 | 0.6485 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 5.1.3 A nivel de evaluación del clima laboral, el Comité podrá proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Trámite de las quejas por etapas  Primera etapa: Recepción de la queja  El Comité  |
| 3 | 0.6417 | convivencia_laboral/manual/quejas_denuncias.md | child |  | Evidencia (opcional): Adjunta correos, mensajes, testimonios, grabaciones o cualquier soporte que ayude a sustentar la denuncia.  Llenado del formato de reporte:  Descargar el formato especifico de queja o denuncia por a |
| 4 | 0.6369 | convivencia_laboral/reglamento_comite/funciones_comite.md | child |  | 5.1.3 A nivel de evaluacion del clima laboral, el Comite podra proponer o hacer recomendaciones al respecto.  5.2 Funciones correctivas:  Tramite de las quejas por etapas  Primera etapa: Recepcion de la queja  El Comite  |
| 5 | 0.6345 | convivencia_laboral/manual/quejas_denuncias.md | child |  | En caso de considerar que esta siendo victima de acoso, conforme a lo establecido en la Ley 1010, se solicita diligenciar el formato correspondiente y remitirlo al correo electronico convivencia@syc.com.co.  Esta queja s |
| 6 | 0.6291 | general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md | child |  | Recibir y dar tramite a las quejas presentadas referentes a acoso laboral. Examinar de manera confidencial los casos especificos o puntuales en los que se formule queja o reclamo, que pudieran tipificar conductas o circu |
| 7 | 0.6099 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Para tal fin, la política responde a los siguientes compromisos:  - Establecer los mecanismos mediante los cuales se garantiza y se ejerce el derecho a  la desconexión laboral, considerando el adecuado uso de las tecnolo |
| 8 | 0.6088 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  6. Derecho a ser escuchado por el comité de convivencia cuando identifique conductas que atenten contra la convivencia laboral de la empresa. (Incluyendo maltrato laboral o conductas de acoso).  |

### Que derechos tienen los trabajadores en convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6766 | convivencia_laboral/manual/derechos_convivencia.md | child |  | 1. Derecho a ser respetado.  2. Derecho a recibir un trato digno frente a creencias religiosas o identidad sexual.  3. Derecho a manifestar su opinion o emociones.  4. Derecho a ser escuchado cuando expone un argumento o |
| 2 | 0.6609 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  DEBERES DE CONVIVENCIA  La calidad de los servidores enaltece a los miembros de la empresa, además todos tienen el deber de engrandecerla y dignificarla. Son deberes de los funcionarios las acá  |
| 3 | 0.6575 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Para tal fin, la política responde a los siguientes compromisos:  - Establecer los mecanismos mediante los cuales se garantiza y se ejerce el derecho a  la desconexión laboral, considerando el adecuado uso de las tecnolo |
| 4 | 0.6456 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | - Garantizar los mecanismos y medios para que los trabajadores, puedan  presentar queja frente a la' posible vulneración de este derecho. Tener en cuenta que los horarios laborales están definidos de acuerdo al proyecto  |
| 5 | 0.6326 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  6. Derecho a ser escuchado por el comité de convivencia cuando identifique conductas que atenten contra la convivencia laboral de la empresa. (Incluyendo maltrato laboral o conductas de acoso).  |
| 6 | 0.6147 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 7 | 0.6139 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 8 | 0.6083 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • Incentivar la participación de los distintos estamentos en las diferentes actividades.  El presente manual de convivencia se aplicará en las relaciones de orden laboral, en la empresa.  MARCO  |

### Que deberes de convivencia laboral deben cumplir los trabajadores?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7032 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  DEBERES DE CONVIVENCIA  La calidad de los servidores enaltece a los miembros de la empresa, además todos tienen el deber de engrandecerla y dignificarla. Son deberes de los funcionarios las acá  |
| 2 | 0.6527 | convivencia_laboral/manual/introduccion.md | child |  | Es importante que existan unas normas de convivencia claras que permitan regular las relaciones que se dan al interior de la empresa, evitando con ello que se afecte el ambiente laboral. No esta demas informar que las no |
| 3 | 0.6461 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Para tal fin, la política responde a los siguientes compromisos:  - Establecer los mecanismos mediante los cuales se garantiza y se ejerce el derecho a  la desconexión laboral, considerando el adecuado uso de las tecnolo |
| 4 | 0.6423 | convivencia_laboral/manual/normas_convivencia.md | child |  | 9. Hacer uso adecuado y respetuoso de las zonas comunes y puestos de trabajo, garantizando que permanezcan limpios y ordenados.  Conductas asociadas:  • Respetar el espacio de trabajo compartido.  • Evitar interrumpir la |
| 5 | 0.6419 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 66: Los trabajadores tienen como deberes los siguientes:  a) Respeto y subordinación a los superiores. b) Respetar a sus compañeros de trabajo. c) Procurar completa armonía e inteligencia con sus superiores y co |
| 6 | 0.6356 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 7 | 0.6343 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 72. Son también obligaciones de los trabajadores.  1. Suministrar inmediatamente y ajustándose a la verdad, las informaciones y datos que tengan relación con el trabajo desempeñado. 2. Registrar en las oficinas  |
| 8 | 0.6200 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | - Garantizar los mecanismos y medios para que los trabajadores, puedan  presentar queja frente a la' posible vulneración de este derecho. Tener en cuenta que los horarios laborales están definidos de acuerdo al proyecto  |

### Que principios y valores orientan la convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6577 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Los principios a los cuales se refiere el siguiente manual tienen como objetivo fundamental establecer un referente ético, para guiar las actitudes, prácticas y formas de actuación de los servidores de la empresa.  1. Re |
| 2 | 0.6373 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • RESPETO: Los trabajadores debemos brindar a los externos e internos un trato digno, amable y tolerante, además demostramos siempre espíritu de servicio.  • EQUIDAD: Los trabajadores deben impl |
| 3 | 0.6349 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | La empresa promueve ambientes de trabajo dignos, respetuosos, seguros y saludables, en los que se garantice la armonía, la integridad física y emocional, la igualdad de trato y el respeto por los derechos de todas las pe |
| 4 | 0.6270 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • No juzgar por la primera impresión y basado en comentarios o percepciones subjetivas.  • Mantener los problemas bajo control dentro del proceso que se gestó, en la medida que sea posible.  7.  |
| 5 | 0.6220 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 6 | 0.6120 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  MANUAL DE CONVIVENCIA LABORAL SISTEMAS Y COMPUTADORES S.A.  INTRODUCCIÓN  Con el ánimo de fomentar un trato amable y respetuoso entre compañeros se diseña el presente Manual de Convivencia Labor |
| 7 | 0.6076 | convivencia_laboral/manual/normas_convivencia.md | child |  | 9. Hacer uso adecuado y respetuoso de las zonas comunes y puestos de trabajo, garantizando que permanezcan limpios y ordenados.  Conductas asociadas:  • Respetar el espacio de trabajo compartido.  • Evitar interrumpir la |
| 8 | 0.5984 | convivencia_laboral/manual/introduccion.md | child |  | Es importante que existan unas normas de convivencia claras que permitan regular las relaciones que se dan al interior de la empresa, evitando con ello que se afecte el ambiente laboral. No esta demas informar que las no |

### En que consiste la politica de desconexion laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7497 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | \| POLÍTICA DE DESCONEXIÓN LABORAL UN |
| 2 | 0.7201 | convivencia_laboral/manual/politica_desconexion.md | child |  | En cumplimiento de lo dispuesto por la ley 2191 de 2022, Sistemas y computadores SA, crea la Politica de Desconexion laboral, la cual esta alineada con el compromiso de la compania, para que exista un balance entre la vi |
| 3 | 0.7184 | general_sst/capacitaciones/politica_seguridad_trabajo/desconexion_laboral_info.md | child |  | En cumplimiento de lo dispuesto por la ley 2191 de 2022, Sistemas y computadores SA, crea la Politica de Desconexion laboral, la cual esta alineada con el compromiso de la compania, para que exista un balance entre la vi |
| 4 | 0.6989 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO POLÍTICA DE DESCONEXION LABORAL NIVEL DE "CODIGO PL.RH-035ST \| CLASIFICACIÓN \| USO INTERNO (NC2) Y ETIQUETADO ? POLÍTICA DE DESCON EXIÓN LABORAL Sistemas y Com |
| 5 | 0.6858 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 95 Política de desconexión laboral. La empresa reconoce y garantiza el derecho de  desconexión laboral de todas las personas trabajadoras. Finalizada la jornada, no estarán obligadas a responder comunicaciones,  |
| 6 | 0.6550 | convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf | child |  | plimiento de lo dispuesto por la ley 2191 de 2022, Sistemas y computadores a la Política de Desconexión laboral, la cual está alineada con el compromiso mpañía, pára que exista un balance entre la vida laboral y familiar |
| 7 | 0.6291 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Para tal fin, la política responde a los siguientes compromisos:  - Establecer los mecanismos mediante los cuales se garantiza y se ejerce el derecho a  la desconexión laboral, considerando el adecuado uso de las tecnolo |
| 8 | 0.5933 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  SYC se compromete a garantizar la igualdad de oportunidades y a proteger a todas las personas, sin distinción de religión, ideología, origen étnico o cultural, discapacidad, edad, estado civil,  |

### Que normas de convivencia deben cumplir los trabajadores?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7038 | convivencia_laboral/manual/introduccion.md | child |  | Es importante que existan unas normas de convivencia claras que permitan regular las relaciones que se dan al interior de la empresa, evitando con ello que se afecte el ambiente laboral. No esta demas informar que las no |
| 2 | 0.6923 | convivencia_laboral/manual/normas_convivencia.md | child |  | 9. Hacer uso adecuado y respetuoso de las zonas comunes y puestos de trabajo, garantizando que permanezcan limpios y ordenados.  Conductas asociadas:  • Respetar el espacio de trabajo compartido.  • Evitar interrumpir la |
| 3 | 0.6626 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  MANUAL DE CONVIVENCIA LABORAL SISTEMAS Y COMPUTADORES S.A.  INTRODUCCIÓN  Con el ánimo de fomentar un trato amable y respetuoso entre compañeros se diseña el presente Manual de Convivencia Labor |
| 4 | 0.6617 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • RESPETO: Los trabajadores debemos brindar a los externos e internos un trato digno, amable y tolerante, además demostramos siempre espíritu de servicio.  • EQUIDAD: Los trabajadores deben impl |
| 5 | 0.6466 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  DEBERES DE CONVIVENCIA  La calidad de los servidores enaltece a los miembros de la empresa, además todos tienen el deber de engrandecerla y dignificarla. Son deberes de los funcionarios las acá  |
| 6 | 0.6463 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 7 | 0.6420 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | La empresa promueve ambientes de trabajo dignos, respetuosos, seguros y saludables, en los que se garantice la armonía, la integridad física y emocional, la igualdad de trato y el respeto por los derechos de todas las pe |
| 8 | 0.6416 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • No juzgar por la primera impresión y basado en comentarios o percepciones subjetivas.  • Mantener los problemas bajo control dentro del proceso que se gestó, en la medida que sea posible.  7.  |

### Que marco legal soporta el comite y la convivencia laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6465 | general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md | child |  | Se cuenta con el comite de convivencia laboral dando cumplimiento a lo establecido en las resoluciones 652 y 1356 de 2012, creado como medida preventiva para el acoso laboral. Sesiona de manera trimestral o en casos que  |
| 2 | 0.6354 | convivencia_laboral/reglamento_comite/objetivo_comite.md | child |  | El Comite de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demas reglamentos de SYC, a la prevencion y solucion de las situaciones causadas por conductas de acoso l |
| 3 | 0.6048 | convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf | child |  | 0.0  CLASIFICACIÓN (NC2)  1. CAPÍTULO PRIMERO  OBJETIVO DEL COMITÉ DE CONVIVENCIA LABORAL  El Comité de Convivencia Laboral tiene por objeto contribuir con mecanismos alternativos a los establecidos en los demás reglamen |
| 4 | 0.6018 | convivencia_laboral/manual/marco_legal.md | child |  | · Resolucion 652 de 2012: “por la cual se establece la conformacion y funcionamiento del Comite de Convivencia Laboral en entidades publicas y empresas privadas y se dictan otras disposiciones.” Modificada por la Resoluc |
| 5 | 0.5988 | general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md | child |  | Recibir y dar tramite a las quejas presentadas referentes a acoso laboral. Examinar de manera confidencial los casos especificos o puntuales en los que se formule queja o reclamo, que pudieran tipificar conductas o circu |
| 6 | 0.5972 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 7 | 0.5950 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 93. Para los efectos relacionados con la búsqueda de solución de las conductas de  acoso laboral y sexual, se establece el siguiente procedimiento interno con el cual se pretende desarrollar las características  |
| 8 | 0.5784 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Para tal fin, la política responde a los siguientes compromisos:  - Establecer los mecanismos mediante los cuales se garantiza y se ejerce el derecho a  la desconexión laboral, considerando el adecuado uso de las tecnolo |

### Que dice la politica de prevencion del acoso laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7097 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO POLÍTICA DE PREVENCION DE ACOSO LABORAL J : NIVEL DE CODIGO PL.RH-01SST \| CLASIFICACIÓN \| USO INTERNO (NC2) \| Versión Y ETIQUETADO POLITICA DE PREVENCIÓN DE A |
| 2 | 0.6962 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_acoso_laboral.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |
| 3 | 0.6878 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | CLAVIJO REPRESENTANTE LEGAL PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO C , 7 POLÍTICA DE PREVENCION DE ACOSO LABORAL .. sy Computadores S.A, , NIVEL DE [CODIGO PLaorssT [CLASIRCACIÓN USO INTERNO (NC2) Ver |
| 4 | 0.6834 | convivencia_laboral/manual/politica_convivencia.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |
| 5 | 0.6744 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 90. Medidas preventivas y correctivas del acoso laboral y sexual: La empresa proveerá  de mecanismos de prevención de las conductas de acoso laboral, sexual y de diversidad de género, estableciendo un procedimie |
| 6 | 0.6456 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | Se prohíben de manera expresa todas las conductas amenazantes, intimidantes, abusivas, coercitivas, discriminatorias o que vulneren la dignidad humana, sin importar su origen o manifestación. Para este fin, se cuenta con |
| 7 | 0.6435 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • Incentivar la participación de los distintos estamentos en las diferentes actividades.  El presente manual de convivencia se aplicará en las relaciones de orden laboral, en la empresa.  MARCO  |
| 8 | 0.6338 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  MANUAL DE CONVIVENCIA LABORAL SISTEMAS Y COMPUTADORES S.A.  INTRODUCCIÓN  Con el ánimo de fomentar un trato amable y respetuoso entre compañeros se diseña el presente Manual de Convivencia Labor |

### Que es la sala amiga de la familia lactante?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6100 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/ventajas_sala_amigas.md | child |  | Sistemas y computadores S.A. cuenta con salas amigas, es un espacio comodo, amigable y con todas las normas tecnico-sanitarias, para las trabajadoras en periodo de lactancia; con el fin de que cada una puede tener su ban |
| 2 | 0.5643 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/sala_amiga_info.md | child |  | Sistemas y Computadores S.A., fomenta espacios que promueven la lactancia materna en el entorno laboral entre las mujeres gestantes y en periodo de lactancia, contribuyendo a la salud fisica y psicologica de la madre y e |
| 3 | 0.4429 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/sala_amiga_info.md | child |  | - Implementar espacios de aprendizaje, fomentando saberes, conocimientos y practicas, referidas a la lactancia materna, alimentacion saludable y desarrollo infantil, en mujeres gestantes y madres en lactancia.  - Cumplir |
| 4 | 0.4349 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/ventajas_sala_amigas.md | child |  | • Contar con una alimentacion adecuada, influye positivamente en el desarrollo inmunologico de los ninos y ninas, en su capacidad de respuesta a las enfermedades, en la frecuencia y gravedad de las mismas.  • La leche ma |
| 5 | 0.3768 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | anteriormente. En los gastos de traslado del trabajador, se entienden comprendidos los de familiares que con él convivieren.  10. Conceder a las trabajadoras que estén en período de lactancia los descansos ordenados por  |
| 6 | 0.3668 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • Incentivar la participación de los distintos estamentos en las diferentes actividades.  El presente manual de convivencia se aplicará en las relaciones de orden laboral, en la empresa.  MARCO  |
| 7 | 0.3596 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  Es un organismo constituido obligatoriamente al interior de la empresa, como una medida preventiva de Acoso Laboral que contribuye a proteger a los trabajadores contra los riesgos psicosociales  |
| 8 | 0.3544 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | \| |

### Cuales son las ventajas de la sala amiga?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5638 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/ventajas_sala_amigas.md | child |  | Sistemas y computadores S.A. cuenta con salas amigas, es un espacio comodo, amigable y con todas las normas tecnico-sanitarias, para las trabajadoras en periodo de lactancia; con el fin de que cada una puede tener su ban |
| 2 | 0.4688 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 4.2 BENEFICIOS  AUMENTAN DISMINUYEN Mejora la salud física y mental de los Menor riesgo de accidentes trabajadores. laborales. Incremento de la concentración y la Reducción del estrés y la fatiga productividad. laboral.  |
| 3 | 0.4296 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Adelantar reuniones con el fin de crear espacios de dialogo entre las partes involucradas, promoviendo compromisos mutuos para llegar a una solución efectiva de los conflictos.  OBJETIVOS ESPECÍFICOS:  • Promover un ambi |
| 4 | 0.4289 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • No juzgar por la primera impresión y basado en comentarios o percepciones subjetivas.  • Mantener los problemas bajo control dentro del proceso que se gestó, en la medida que sea posible.  7.  |
| 5 | 0.4203 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Reduce el estres y mejora el bienestar emocional: Las pausas activas proporcionan un alivio instantaneo del estres acumulado. Estirarse, respirar profundamente o dar un paseo corto pueden ayudar a reducir la tension fisi |
| 6 | 0.4044 | convivencia_laboral/manual/normas_convivencia.md | child |  | • No patrocinar el chisme y el rumor.  • Evitar que los comentarios afecten la integridad de las personas, el clima laboral y el logro de los objetivos institucionales.  • Respetar la vida privada de los companeros de tr |
| 7 | 0.4032 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 8 | 0.3997 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/sala_amiga_info.md | child |  | Sistemas y Computadores S.A., fomenta espacios que promueven la lactancia materna en el entorno laboral entre las mujeres gestantes y en periodo de lactancia, contribuyendo a la salud fisica y psicologica de la madre y e |

### Donde esta ubicada la sala amiga y quienes pueden usarla?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5037 | general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/ventajas_sala_amigas.md | child |  | Sistemas y computadores S.A. cuenta con salas amigas, es un espacio comodo, amigable y con todas las normas tecnico-sanitarias, para las trabajadoras en periodo de lactancia; con el fin de que cada una puede tener su ban |
| 2 | 0.4098 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | \| |
| 3 | 0.3988 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Dicho programa se pondrá en marcha en caso de evidenciarse acoso laboral por parte del comité de convivencia laboral. El programa se estructura en cuatro (4) fases:  1. Primera Fase: Valoración: Entre las partes a saber, |
| 4 | 0.3843 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | Adelantar reuniones con el fin de crear espacios de dialogo entre las partes involucradas, promoviendo compromisos mutuos para llegar a una solución efectiva de los conflictos.  OBJETIVOS ESPECÍFICOS:  • Promover un ambi |
| 5 | 0.3748 | convivencia_laboral/manual/objetivos_especificos_comite.md | child |  | · Promover un ambiente adecuado para la convivencia, el orden y el bienestar laboral dentro de la empresa.  · Estimular diferentes mecanismos de convivencia armonica ademas prevencion en la empresa.  · Incentivar la part |
| 6 | 0.3719 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • Incentivar la participación de los distintos estamentos en las diferentes actividades.  El presente manual de convivencia se aplicará en las relaciones de orden laboral, en la empresa.  MARCO  |
| 7 | 0.3700 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Bucaramanga Centro Empresarial Ecoparque Natura Torre 3 Piso 8 Tel: (7)6343558 - Fax: (7)6455869 www.syc.com.co  • Sabotaje, manipulación o alteración de sistemas, redes o dispositivos tecnológicos que afecten la operaci |
| 8 | 0.3690 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Manejar escrupulosamente los valores e intereses que se le encomienden por razón de su cargo y rendir cuenta rigurosa de ellos a La Empresa. 8. Evitar toda desavenencia con los compañeros de trabajo. Bucaramanga Centro E |

### Como solicito o pido vacaciones?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6549 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 39. La época de las vacaciones debe ser señalada por la empresa a más tardar dentro  del año subsiguiente al que se hayan causado y ellas deben ser concedidas oficiosamente o a petición del trabajador, sin perju |
| 2 | 0.5982 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 43. Durante el período de vacaciones el trabajador recibirá el salario ordinario que esté  devengando el día que comience a disfrutar de ellas. En consecuencia, solo se excluirán para la liquidación de vacacione |
| 3 | 0.5966 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 38. Los trabajadores que hubieren prestado sus servicios durante un año, continúo o  discontinuo, tienen derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas. A quienes presten su servicio p |
| 4 | 0.5950 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 35. El descanso semanal compensatorio puede darse en alguna de las siguientes  formas: 1. En otro día laborable de la semana siguiente a todo el personal del establecimiento o por turnos. 2. Desde el medio día o |
| 5 | 0.5826 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 41. En virtud de lo establecido por el artículo 189 del Código Sustantivo del Trabajo, la  Empresa y el trabajador podrán acordar por escrito, previa solicitud del trabajador, que se pague en dinero hasta la mit |
| 6 | 0.5614 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 42. La empresa puede determinar, para todos o parte de sus trabajadores, una época  fija para las vacaciones simultáneas, y si así lo hiciere, los que en tal época no llevaren un año cumplido de servicio, se ent |
| 7 | 0.5572 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | No tiene derecho a la remuneración de descanso dominical, el trabajador que deba recibir por ese mismo día un auxilio o indemnización en dinero por enfermedad o accidente de trabajo. Para los efectos de este artículo, lo |
| 8 | 0.5465 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Cuando las mencionadas festividades caigan en domingo, el descanso remunerado, igualmente se trasladará al lunes. PARÁGRAFO 1. Las prestaciones y derechos que para el trabajador originen el trabajo en los días festivos,  |

### Que tipos de faltas contempla el reglamento interno de trabajo?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6753 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | artículo 76 del presente Reglamento Interno de Trabajo.  2. El descuido, el error o la demora inexplicable en la ejecución de sus funciones labores o cualquier función conexa o anexa al mismo que dependan para el cabal f |
| 2 | 0.6165 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | No comunicar a la empresa los cambios de domicilio o circunstancias personales que puedan afectar su relación y obligaciones con la empresa en un plazo de cinco (5) días después de haberlo efectuado.  8. No cumplir con l |
| 3 | 0.6035 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Presentar al sitio de trabajo bajo notorios efectos de drogas o sustancias alucinógenas.  19. Ingerir bebidas alcohólicas o consumir drogas o sustancias alucinógenas en la jornada  laboral así sea dentro de su descanso o |
| 4 | 0.5999 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | naturaleza, lo cual implicaría una flagrante violación al reglamento de trabajo.  40. El comprometer la empresa frente a terceros sin autorización alguna de sus directivos.  41. Hacer uso del internet y/o correo electrón |
| 5 | 0.5921 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 1: Este Reglamento Interno de Trabajo aplica a SISTEMAS Y COMPUTADORES S.A.,  con domicilio en Floridablanca, y rige para todas sus sedes y agencias en el territorio colombiano. Sus disposiciones son de obligato |
| 6 | 0.5831 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | 32. Cambiar cheques por efectivo de la compañía a personas no autorizadas por la empresa.  33. Entregar dineros de la compañía a personas diferentes a las autorizadas por la Dirección  administrativa y contable de la com |
| 7 | 0.5809 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 76. Las faltas cometidas por los trabajadores en el desempeño de sus funciones  laborales o en representación de la empresa, aun estando fuera del sitio o puesto de trabajo o de las instalaciones de la compañía  |
| 8 | 0.5746 | general_sst/manuales/organizacion/organizacion.md | child |  | Sistemas y Computadores S.A. es responsable de proteger la seguridad y salud de sus trabajadores, conforme al Decreto Ley 1295 de 1994, la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas nor |

### Que sanciones aplican por consumo de alcohol o sustancias psicoactivas?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5813 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_alcohol_drogas/prevencion_alcohol_drogas.md | child |  | SISTEMAS Y COMPUTADORES S.A, al promover un ambiente de trabajo saludable, seguro y exento del consumo de alcohol, tabaco, drogas y cualquier tipo de sustancia que genere dependencia, desarrolla la presente politica dand |
| 2 | 0.5218 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 79. Las sanciones para aplicar son las siguientes:  TIPO SANCIÓN A Llamado de atención escrito B Suspensión del trabajador hasta 3 días laborales. C Suspensión del trabajador hasta 8 días laborales. Bucaramanga  |
| 3 | 0.5021 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Presentar al sitio de trabajo bajo notorios efectos de drogas o sustancias alucinógenas.  19. Ingerir bebidas alcohólicas o consumir drogas o sustancias alucinógenas en la jornada  laboral así sea dentro de su descanso o |
| 4 | 0.4743 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 99. Evaluaciones médicas ocupacionales. La empresa cumplirá la **Resolución 1843  de 2025en materia de evaluaciones médicas ocupacionales (ingreso, periódicas, egreso, postincapacidad, retorno y seguimiento), ma |
| 5 | 0.4656 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | especializado reconocido por el Ministerio de Educación Nacional o en una institución del Sistema Nacional de Bienestar Familiar autorizada para el efecto por el Ministerio de la Protección Social, o que obtenga el certi |
| 6 | 0.4651 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Bucaramanga Centro Empresarial Ecoparque Natura Torre 3 Piso 8 Tel: (7)6343558 - Fax: (7)6455869 www.syc.com.co  • Sabotaje, manipulación o alteración de sistemas, redes o dispositivos tecnológicos que afecten la operaci |
| 7 | 0.4639 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 74. Se prohíbe a los trabajadores:  1. Sustraer de la fábrica, taller o establecimiento, los útiles de trabajo, las materias primas o productos  elaborados, sin permiso de la empresa.  2. Presentarse al trabajo  |
| 8 | 0.4638 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Las burlas sobre la apariencia física o la forma de vestir formuladas en público. 8. La alusión pública a hechos pertenecientes a la intimidad de la persona. 9. La imposición de deberes ostensiblemente extraños a las obl |

### Que dice la politica de prevencion de alcohol y drogas?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6124 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_alcohol_drogas/prevencion_alcohol_drogas.md | child |  | SISTEMAS Y COMPUTADORES S.A, al promover un ambiente de trabajo saludable, seguro y exento del consumo de alcohol, tabaco, drogas y cualquier tipo de sustancia que genere dependencia, desarrolla la presente politica dand |
| 2 | 0.5157 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/seguridad_vial_info.md | child |  | POLITICA DE SEGURIDAD VIAL  Es compromiso de Sistemas y Computadores SA, garantizar los recursos para la planificacion, implementacion, seguimiento y mejora del PESV por medio de actividades de promocion y prevencion de  |
| 3 | 0.4954 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_acoso_laboral.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |
| 4 | 0.4871 | convivencia_laboral/manual/politica_convivencia.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |
| 5 | 0.4848 | general_sst/manuales/planificacion/planificacion_info.md | child |  | La metodologia de identificacion de peligros y valoracion de riesgos, permite la participacion activa de los trabajadores, partes interesadas y la priorizacion de los riesgos para establecer medidas de intervencion con e |
| 6 | 0.4840 | convivencia_laboral/manual/marco_legal.md | child |  | · Resolucion 652 de 2012: “por la cual se establece la conformacion y funcionamiento del Comite de Convivencia Laboral en entidades publicas y empresas privadas y se dictan otras disposiciones.” Modificada por la Resoluc |
| 7 | 0.4803 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 100. Ruta de prevención y atención. Además de lo previsto en la Ley 1010 de 2006, la  empresa implementará una **ruta específica** para la prevención, atención y protección frente al **acoso sexual**: canales co |
| 8 | 0.4797 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | Se prohíben de manera expresa todas las conductas amenazantes, intimidantes, abusivas, coercitivas, discriminatorias o que vulneren la dignidad humana, sin importar su origen o manifestación. Para este fin, se cuenta con |

### Cuando puede la empresa requerir pruebas de deteccion de consumo?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5495 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_alcohol_drogas/prevencion_alcohol_drogas.md | child |  | SISTEMAS Y COMPUTADORES S.A, al promover un ambiente de trabajo saludable, seguro y exento del consumo de alcohol, tabaco, drogas y cualquier tipo de sustancia que genere dependencia, desarrolla la presente politica dand |
| 2 | 0.5189 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 73. Se prohíbe a la empresa:  1. Deducir, retener o compensar suma alguna del monto de los salarios y prestaciones en dinero que  corresponda a los trabajadores, sin autorización previa escrita de éstos para cad |
| 3 | 0.5077 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | No comunicar a la empresa los cambios de domicilio o circunstancias personales que puedan afectar su relación y obligaciones con la empresa en un plazo de cinco (5) días después de haberlo efectuado.  8. No cumplir con l |
| 4 | 0.5046 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | 32. Cambiar cheques por efectivo de la compañía a personas no autorizadas por la empresa.  33. Entregar dineros de la compañía a personas diferentes a las autorizadas por la Dirección  administrativa y contable de la com |
| 5 | 0.5042 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 13: La empresa una vez admitida el aspirante podrá estipular con el por escrito un  periodo inicial de prueba que tendrá por objeto apreciar por parte de la Empresa, las actitudes del trabajador y por parte de é |
| 6 | 0.5042 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | Cualquier disposición anterior que se oponga a la normativa vigente se considera derogada o ajustada, garantizando siempre el respeto a los derechos laborales y a los principios de equidad e inclusión.  CAPÍTULO II CONDI |
| 7 | 0.5024 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | 13. Reconocer el pago de los instrumentos y útiles de trabajo que por su indebida, negligente e  irresponsable utilización sean averiados y/o destruidos.  14. Observar estrictamente lo establecido o lo que establezca La  |
| 8 | 0.4960 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | En virtud de lo establecido por la Ley 1429 de 2010 no podrán realizarse descuentos a los trabajadores así ellos lo autoricen cuando se afecte el salario mínimo o la parte señalada como inembargable por la Ley.  2. Oblig |

### En que consiste el programa o politica de pausas activas?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7106 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  INTRODUCCIÓN  El presente programa de pausas activas tiene como objetivo principal promover la salud y el bienestar de los empleados de la empresa SISTEMAS Y COMPUTADORES S.A. a través de la implementación de pausas |
| 2 | 0.6994 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 4.1 PAUSAS ACTIVAS  Las pausas activas consisten en una serie de ejercicios físicos y mentales realizados de manera consciente y programada durante la jornada laboral. Estas pueden incluir estiramientos musculares, ejerc |
| 3 | 0.6943 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Las pausas activas son periodos de descanso cortos pero intencionados que se toman durante actividades prolongadas y sedentarias. Estas pausas tienen una importancia significativa para el bienestar fisico y mental de las |
| 4 | 0.6708 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  5. METODOLOGIA  El programa se llevará a cabo mediante la realización de sesiones periódicas de pausas activas, las cuales serán coordinadas por el líder a cargo. El cual de acuerdo a la operación establecerán horar |
| 5 | 0.6633 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  2. OBJETIVO GENERAL  Establecer un programa de pausas activas en la empresa SISTEMAS Y COMPUTADORES S.A con el fin de mejorar la salud y el bienestar de los empleados, reducir el ausentismo laboral y aumentar la pro |
| 6 | 0.6330 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  - Colaborar con el equipo de seguridad y salud en el trabajo para garantizar el éxito del programa de pausas activas en el área. - Mantener una comunicación efectiva con los empleados sobre la importancia y los bene |
| 7 | 0.6221 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | • Proporcionar retroalimentación al personal que no cumpla con la realización de las pausas activas, siguiendo un proceso escalonado. El primer llamado será realizado por el líder designado para el área correspondiente,  |
| 8 | 0.6103 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Reduce el estres y mejora el bienestar emocional: Las pausas activas proporcionan un alivio instantaneo del estres acumulado. Estirarse, respirar profundamente o dar un paseo corto pueden ayudar a reducir la tension fisi |

### Por que son importantes las pausas activas para la salud fisica?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.8060 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Las pausas activas son periodos de descanso cortos pero intencionados que se toman durante actividades prolongadas y sedentarias. Estas pausas tienen una importancia significativa para el bienestar fisico y mental de las |
| 2 | 0.7460 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Reduce el estres y mejora el bienestar emocional: Las pausas activas proporcionan un alivio instantaneo del estres acumulado. Estirarse, respirar profundamente o dar un paseo corto pueden ayudar a reducir la tension fisi |
| 3 | 0.6903 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 4.1 PAUSAS ACTIVAS  Las pausas activas consisten en una serie de ejercicios físicos y mentales realizados de manera consciente y programada durante la jornada laboral. Estas pueden incluir estiramientos musculares, ejerc |
| 4 | 0.6837 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  INTRODUCCIÓN  El presente programa de pausas activas tiene como objetivo principal promover la salud y el bienestar de los empleados de la empresa SISTEMAS Y COMPUTADORES S.A. a través de la implementación de pausas |
| 5 | 0.6447 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  - Colaborar con el equipo de seguridad y salud en el trabajo para garantizar el éxito del programa de pausas activas en el área. - Mantener una comunicación efectiva con los empleados sobre la importancia y los bene |
| 6 | 0.6341 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  2. OBJETIVO GENERAL  Establecer un programa de pausas activas en la empresa SISTEMAS Y COMPUTADORES S.A con el fin de mejorar la salud y el bienestar de los empleados, reducir el ausentismo laboral y aumentar la pro |
| 7 | 0.6286 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  OPCIÓN 3 Esta es una rutina básica tanto para personas que trabajan de pie (con manejo de cargas) o sentadas (ya sea en oficina o trabajo repetitivo). Cada uno de los ejercicios se sostiene por espacio de 10 a 15 se |
| 8 | 0.5962 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  1. DESCRIPCIÓN DEL PROBLEMA  La descripción del problema se centra en los efectos adversos del sedentarismo y la exposición prolongada a actividades laborales estáticas en la salud de los trabajadores. Estos problem |

### Como ayudan las pausas activas a la concentracion y al estres?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7633 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Reduce el estres y mejora el bienestar emocional: Las pausas activas proporcionan un alivio instantaneo del estres acumulado. Estirarse, respirar profundamente o dar un paseo corto pueden ayudar a reducir la tension fisi |
| 2 | 0.7357 | general_sst/capacitaciones/pausas_activas/info.md | child |  | Las pausas activas son periodos de descanso cortos pero intencionados que se toman durante actividades prolongadas y sedentarias. Estas pausas tienen una importancia significativa para el bienestar fisico y mental de las |
| 3 | 0.6915 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 4.1 PAUSAS ACTIVAS  Las pausas activas consisten en una serie de ejercicios físicos y mentales realizados de manera consciente y programada durante la jornada laboral. Estas pueden incluir estiramientos musculares, ejerc |
| 4 | 0.6591 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  INTRODUCCIÓN  El presente programa de pausas activas tiene como objetivo principal promover la salud y el bienestar de los empleados de la empresa SISTEMAS Y COMPUTADORES S.A. a través de la implementación de pausas |
| 5 | 0.6343 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  OPCIÓN 3 Esta es una rutina básica tanto para personas que trabajan de pie (con manejo de cargas) o sentadas (ya sea en oficina o trabajo repetitivo). Cada uno de los ejercicios se sostiene por espacio de 10 a 15 se |
| 6 | 0.6123 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  2. OBJETIVO GENERAL  Establecer un programa de pausas activas en la empresa SISTEMAS Y COMPUTADORES S.A con el fin de mejorar la salud y el bienestar de los empleados, reducir el ausentismo laboral y aumentar la pro |
| 7 | 0.6077 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  1. DESCRIPCIÓN DEL PROBLEMA  La descripción del problema se centra en los efectos adversos del sedentarismo y la exposición prolongada a actividades laborales estáticas en la salud de los trabajadores. Estos problem |
| 8 | 0.5837 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 4.3 ACTIVIDADES  • Movilidad articular • Estiramiento • Actividades lúdicas • Actividades de habilidad mental • Sensibilización y capacitación sobre pausas activas • Diseño y planificación de rutinas de pausas activas •  |

### Que recomendaciones de seguridad vial aparecen en el corpus?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5089 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/prevencion_vial.md | child |  | Para reducir el riesgo de accidentes viales y proteger la vida propia y la de los demas, es fundamental adoptar conductas responsables al conducir:  Utilizar siempre el cinturon de seguridad. Senalizar correctamente las  |
| 2 | 0.4733 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | Recuperado de [https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/PP/ENT/a bece-actividad-fisica-entorno-laboral.pdf].  Instituto Colombiano de Normas Técnicas y Certificación (ICONTEC). (2008). Norma  |
| 3 | 0.4470 | general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf | child |  | 0.0  10. BIBLIOGRAFIA  Ministerio de Trabajo de Colombia. Guía Técnica para la Promoción de la Actividad Física en el Ámbito Laboral.  Instituto Colombiano de Normas Técnicas y Certificación (ICONTEC). Norma Técnica Colo |
| 4 | 0.4347 | convivencia_laboral/manual/marco_legal.md | child |  | · Resolucion 652 de 2012: “por la cual se establece la conformacion y funcionamiento del Comite de Convivencia Laboral en entidades publicas y empresas privadas y se dictan otras disposiciones.” Modificada por la Resoluc |
| 5 | 0.4346 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 100. Ruta de prevención y atención. Además de lo previsto en la Ley 1010 de 2006, la  empresa implementará una **ruta específica** para la prevención, atención y protección frente al **acoso sexual**: canales co |
| 6 | 0.4270 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | • Ley 2365 de 2024: “Por medio de la cual se adoptan medidas de prevención, protección y atención del acoso sexual en el ámbito laboral y en las instituciones de educación superior en Colombia”. Importante porque aclara  |
| 7 | 0.4240 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf | child |  | OBJETIVOS Y METAS SEGURIDAD VIAL  SISTEMAS Y COMPUTADORES S.A se ha establecido los objetivos y metas que permiten planear de manera estratégica la seguridad vial.  La matriz define indicadores de medición que permiten r |
| 8 | 0.4193 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | máquinas particularmente peligrosas.  17. Trabajos de vidrio y alfarería, trituración y mezclado de materia prima; trabajo de hornos,  pulido y esmerilado en seco de vidriería, operaciones de limpieza por chorro de arena |

### Que compromisos tiene el PESV o plan estrategico de seguridad vial?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.7041 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/seguridad_vial_info.md | child |  | POLITICA DE SEGURIDAD VIAL  Es compromiso de Sistemas y Computadores SA, garantizar los recursos para la planificacion, implementacion, seguimiento y mejora del PESV por medio de actividades de promocion y prevencion de  |
| 2 | 0.6374 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf | child |  | OBJETIVOS Y METAS SEGURIDAD VIAL  SISTEMAS Y COMPUTADORES S.A se ha establecido los objetivos y metas que permiten planear de manera estratégica la seguridad vial.  La matriz define indicadores de medición que permiten r |
| 3 | 0.4616 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf | child |  | vial programadas por trimestre) trabajadores como actores de *100 la vía, a través de mecanismos de campañas y/o sensibilizaciones. Realizar seguimiento periódico 100% de los vehículos (# de vehiculos inspeccionados a ca |
| 4 | 0.4610 | general_sst/manuales/introduccion.md | child |  | SISTEMAS Y COMPUTADORES S.A., en cumplimiento de la Ley 1562 de 2012, el Decreto 1072 de 2015, la Resolucion 0312 de 2019 y demas normatividad vigente en materia de riesgos laborales, ha estructurado su Sistema de Gestio |
| 5 | 0.4480 | general_sst/manuales/planificacion/planificacion_info.md | child |  | OBJETIVOS:  En coherencia con la politica de seguridad y salud en el trabajo se ha establecido los objetivos que permiten planear de manera estrategica el sistema de gestion de la seguridad y salud en el trabajo:  Manten |
| 6 | 0.4344 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/prevencion_vial.md | child |  | Para reducir el riesgo de accidentes viales y proteger la vida propia y la de los demas, es fundamental adoptar conductas responsables al conducir:  Utilizar siempre el cinturon de seguridad. Senalizar correctamente las  |
| 7 | 0.4315 | general_sst/manuales/organizacion/arl/funciones_responsabilidades.md | child |  | Capacitar al Comite Paritario de Seguridad y Salud en el Trabajo en los aspectos relativos al SG-SST y prestar asesoria y asistencia tecnica a sus empresas y trabajadores afiliados, en la implementacion del SG-SST. Brind |
| 8 | 0.4149 | general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf | child |  | l l Proteger: la seguridad y: salud «de todos los trabajadores, mediante la mejora continua del Sistema de Gestión de la Seguridad y Salud en el Trabajo. Destinar los recursos financieros, humanos, técnicos, físicos y la |

### Que significa cero tolerancia frente a alcohol y sustancias en seguridad vial?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.5155 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/seguridad_vial_info.md | child |  | POLITICA DE SEGURIDAD VIAL  Es compromiso de Sistemas y Computadores SA, garantizar los recursos para la planificacion, implementacion, seguimiento y mejora del PESV por medio de actividades de promocion y prevencion de  |
| 2 | 0.5058 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_alcohol_drogas/prevencion_alcohol_drogas.md | child |  | SISTEMAS Y COMPUTADORES S.A, al promover un ambiente de trabajo saludable, seguro y exento del consumo de alcohol, tabaco, drogas y cualquier tipo de sustancia que genere dependencia, desarrolla la presente politica dand |
| 3 | 0.4889 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/prevencion_vial.md | child |  | Para reducir el riesgo de accidentes viales y proteger la vida propia y la de los demas, es fundamental adoptar conductas responsables al conducir:  Utilizar siempre el cinturon de seguridad. Senalizar correctamente las  |
| 4 | 0.4792 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | Se prohíben de manera expresa todas las conductas amenazantes, intimidantes, abusivas, coercitivas, discriminatorias o que vulneren la dignidad humana, sin importar su origen o manifestación. Para este fin, se cuenta con |
| 5 | 0.4727 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf | child |  | vial programadas por trimestre) trabajadores como actores de *100 la vía, a través de mecanismos de campañas y/o sensibilizaciones. Realizar seguimiento periódico 100% de los vehículos (# de vehiculos inspeccionados a ca |
| 6 | 0.4590 | general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf | child |  | OBJETIVOS Y METAS SEGURIDAD VIAL  SISTEMAS Y COMPUTADORES S.A se ha establecido los objetivos y metas que permiten planear de manera estratégica la seguridad vial.  La matriz define indicadores de medición que permiten r |
| 7 | 0.4555 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_acoso_laboral.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |
| 8 | 0.4504 | convivencia_laboral/manual/politica_convivencia.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |

### Que documentos o reglas hablan de prevencion del acoso laboral?

| # | score | documento | rol | seccion | chunk |
|---|------:|-----------|-----|---------|-------|
| 1 | 0.6780 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  • Incentivar la participación de los distintos estamentos en las diferentes actividades.  El presente manual de convivencia se aplicará en las relaciones de orden laboral, en la empresa.  MARCO  |
| 2 | 0.6560 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | 0.2  CLASIFICACIÓN (NC2)  MANUAL DE CONVIVENCIA LABORAL SISTEMAS Y COMPUTADORES S.A.  INTRODUCCIÓN  Con el ánimo de fomentar un trato amable y respetuoso entre compañeros se diseña el presente Manual de Convivencia Labor |
| 3 | 0.6556 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO POLÍTICA DE PREVENCION DE ACOSO LABORAL J : NIVEL DE CODIGO PL.RH-01SST \| CLASIFICACIÓN \| USO INTERNO (NC2) \| Versión Y ETIQUETADO POLITICA DE PREVENCIÓN DE A |
| 4 | 0.6410 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 90. Medidas preventivas y correctivas del acoso laboral y sexual: La empresa proveerá  de mecanismos de prevención de las conductas de acoso laboral, sexual y de diversidad de género, estableciendo un procedimie |
| 5 | 0.6398 | convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf | child |  | • Ley 2365 de 2024: “Por medio de la cual se adoptan medidas de prevención, protección y atención del acoso sexual en el ámbito laboral y en las instituciones de educación superior en Colombia”. Importante porque aclara  |
| 6 | 0.6323 | convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf | child |  | CLAVIJO REPRESENTANTE LEGAL PROCESOS ADMINISTRATIVOS / SEGURIDAD Y SALUD EN EL TRABAJO C , 7 POLÍTICA DE PREVENCION DE ACOSO LABORAL .. sy Computadores S.A, , NIVEL DE [CODIGO PLaorssT [CLASIRCACIÓN USO INTERNO (NC2) Ver |
| 7 | 0.6314 | general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf | child |  | ARTÍCULO 91. Los mecanismos de prevención de las conductas de acoso laboral y sexual previstos  por la empresa constituyen actividades tendientes a generar una conciencia colectiva conviviente que promueva el trabajo en  |
| 8 | 0.6272 | general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_acoso_laboral.md | child |  | Sistemas y Computadores S.A., en cumplimiento de la normatividad vigente relacionada con la convivencia laboral, adopta la presente Politica de Prevencion de Acoso Laboral, la cual integra de manera general las acciones  |

## Documentos incluidos

- `convivencia_laboral/manual/1761580555950_syc_RE.RH-04SST23102025.pdf`
- `convivencia_laboral/manual/1772036012249_syc_mrh03sstmanualdeconv.pdf`
- `convivencia_laboral/manual/1781045303349_syc_politicadedesconexin.pdf`
- `convivencia_laboral/manual/1781045390931_syc_politicadeprevencind.pdf`
- `convivencia_laboral/manual/deberes_convivencia.md`
- `convivencia_laboral/manual/derechos_convivencia.md`
- `convivencia_laboral/manual/funciones_comite-.md`
- `convivencia_laboral/manual/introduccion.md`
- `convivencia_laboral/manual/marco_legal.md`
- `convivencia_laboral/manual/normas_convivencia.md`
- `convivencia_laboral/manual/objetivo_general_comite.md`
- `convivencia_laboral/manual/objetivos_especificos_comite.md`
- `convivencia_laboral/manual/politica_convivencia.md`
- `convivencia_laboral/manual/politica_desconexion.md`
- `convivencia_laboral/manual/principios_convivencia.md`
- `convivencia_laboral/manual/quejas_denuncias.md`
- `convivencia_laboral/manual/valores.md`
- `convivencia_laboral/reglamento_comite/1761609513260_syc_RG.RH-01-SST23102025.pdf`
- `convivencia_laboral/reglamento_comite/conformacion_comite.md`
- `convivencia_laboral/reglamento_comite/funcionamiento_comite.md`
- `convivencia_laboral/reglamento_comite/funciones_comite.md`
- `convivencia_laboral/reglamento_comite/metodologia_sesiones_comite.md`
- `convivencia_laboral/reglamento_comite/objetivo_comite.md`
- `convivencia_laboral/reglamento_comite/vigencias_modificaciones_comite.md`
- `copasst/comunicacion.md`
- `copasst/funciones_copasst.md`
- `copasst/funciones_presidente_copasst.md`
- `copasst/funciones_secretario_copasst.md`
- `copasst/miembros_copasst_2025_2027.md`
- `general_sst/capacitaciones/pausas_activas/1711493199040_syc_pg-rh-10-sst.program.pdf`
- `general_sst/capacitaciones/pausas_activas/info.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/desconexion_laboral_info.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_acoso_laboral.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/prevencion_alcohol_drogas/prevencion_alcohol_drogas.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/sala_amiga_info.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/sala_amigas/ventajas_sala_amigas.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/1768504433896_syc_1723156961461_syc_vial.pdf`
- `general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/prevencion_vial.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/seguridad_vial/seguridad_vial_info.md`
- `general_sst/capacitaciones/politica_seguridad_trabajo/sgsst_info.md`
- `general_sst/manuales/aplicacion/aplicacion_info.md`
- `general_sst/manuales/auditoria/auditoria_info.md`
- `general_sst/manuales/introduccion.md`
- `general_sst/manuales/mejora/mejora_info.md`
- `general_sst/manuales/organizacion/arl/funciones_responsabilidades.md`
- `general_sst/manuales/organizacion/comite_convivencia_laboral/aspectos_juridicos_laborales.md`
- `general_sst/manuales/organizacion/comite_convivencia_laboral/funciones_responsabilidades.md`
- `general_sst/manuales/organizacion/copasst/Aspectos_juridicos_laborales.md`
- `general_sst/manuales/organizacion/copasst/Funciones_Responsabilidades.md`
- `general_sst/manuales/organizacion/organizacion.md`
- `general_sst/manuales/organizacion/reglamento_interno_trabajo/1780069704133_syc_REGLAMENTOACTUALIZADO29052026.pdf`
- `general_sst/manuales/planificacion/planificacion_info.md`
- `general_sst/manuales/politica/1778000305710_syc_politicadeseguridady.pdf`
- `general_sst/manuales/politica/politica.md`
- `general_sst/manuales/verificacion/verificacion_info.md`
