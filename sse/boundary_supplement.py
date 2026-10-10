import csv,pathlib
B=pathlib.Path(__file__).parent
U24='https://www.sse.com/media/0aibgke4/sse_ar24_interactive.pdf'
U23='https://www.sse.com/media/dncdjrcw/sse-annual-report-2023-web-final.pdf'
US='https://www.sse.com/media/nardc12j/sse-plc-sustainability-report-2024.pdf'
UP='https://www.sse.com/media/ej5l4w14/sse-plc_prospectus-2024_final-version.pdf'
def write(name,rows):
 with(B/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
cells=[]
for y,metric,val,unit,url,page,col,status in [
(2024,'gas_oil_capacity_gb',5538,'MW',U24,'p78 Thermal KPI','March2024','reported_verified_supplement'),
(2024,'enterprise_biomass_heat_other_output',105,'GWh',U24,'p82 Enterprise KPI','March2024','reported_mixed_energy_not_fossil_electricity'),
(2023,'enterprise_biomass_heat_other_output',96,'GWh',U24,'p82 Enterprise KPI','March2023','reported_mixed_energy_not_fossil_electricity'),
(2022,'enterprise_biomass_heat_other_output',104,'GWh',U23,'p110–111 Distributed Energy KPI;PDF56','March2022','reported_mixed_energy_not_fossil_electricity'),
(2024,'renewable_total_sustainability_including_biomass_storage',10004,'GWh',US,'p36–37 performance summary','2023/24','reported_alternate_definition'),
(2023,'renewable_total_sustainability_including_biomass_storage',9665,'GWh',US,'p36–37 performance summary','2022/23','reported_alternate_definition'),
(2022,'renewable_total_sustainability_including_biomass_storage',8799,'GWh',US,'p36–37 performance summary','2021/22','reported_alternate_definition')]:
 cells.append(dict(issuer='SSE',fiscal_year_end=y,metric=metric,value=val,unit=unit,value_status=status,source_url=url,source_locator=page,source_column=col,verification='official_web_PDF_text',retrieved='2026-10-10'))
write('boundary_additional_source_cells.csv',cells)
bridge=[]
for region,start,end,closure in [('GB',5538,5538,0),('ROI',1292,672,-620),('Total',6830,6210,-620)]:
 bridge.append(dict(issuer='SSE',period_start='2023-03-31',period_end='2024-03-31',region=region,start_mw=start,end_mw=end,reported_net_change_mw=end-start,identified_closure_change_mw=closure,accounting_reconciliation_residual_mw=end-start-closure,gross_additions_mw='',gross_disposals_mw='',other_gross_changes_mw='',gross_components_status='not_exhaustively_verified',residual_interpretation='arithmetic_only;zero_is_not_proof_of_no_offsetting_gross_changes',capacity_basis='TransmissionEntryCapacity;owned_plus_JV_share',source_url=U24,source_locator='p78 Thermal KPI and note2',closure_source_url=UP,closure_source_locator='p105'))
write('thermal_capacity_bridge_2023_2024.csv',bridge)
flags=[
('Marchwood','contractual_vs_ownership_boundary','all_pilot_years','50pct_equity;100pct_output_PPA','reported_thermal_output_not_equity_only','',U23,'p106–107 Thermal KPI note2 and contracts footnote'),
('Seabank','contract_expiry_and_reporting_boundary','2021-09','100pct_PPA_to50pct_equity','FY2022_spans_two_boundaries;not_retirement','',U23,'p106–107 Thermal KPI note2'),
('Triton Power','ownership_acquisition','2022-09-01','acquired_portfolio_entered_scope','FY2023_partial_year;FY2024_full_year','',U23,'p106–107 Thermal KPI note1'),
('Keadby2','physical_commissioning_and_output_exclusion','2023-03-15','1184GWh_precommissioning_excluded_FY2023','constant_physical_output_series_not_yet_recovered','',U24,'p78 Thermal KPI note4'),
('Tarbert','physical_closure','2023-12','620MW_old_oil_station_closed','capacity_event_not_quantified_generation_effect','',UP,'p105'),
('Enterprise','unresolved_fuel_and_energy_boundary','2022–2024','biomass_heat_and_other_output_reported_separately','whole_company_fossil_generation_residual_NA','',U24,'p82'),
('Biomass','renewable_segment_exclusion','2022–2024','73/68/78GWh_outside_renewables_segment','FY2024_cross_report1GWh_discrepancy','',U24,'p75 note4; sustainability2024pp36–37'),
('Coal','historical_physical_closure','2020','last_coal_station_closed','supports_historical_exit_but_no_numeric_coal_cell_added','', 'https://www.sse.com/media/vodhr2aw/sse-plc-sustainability-report-2024.pdf','pp20–21'),
('Emissions','operational_control_vs_equity_boundary','2022–2024','Seabank50pct_emissions_in_scope3','do_not_pair_raw_scope1_with_equity_output_without_alignment','', 'https://www.sse.com/media/vodhr2aw/sse-plc-sustainability-report-2024.pdf','pp20–21')]
write('boundary_classification_ledger.csv',[dict(asset_or_component=a,change_type=b,date=c,source_fact=d,consequence=e,quantified_generation_adjustment_gwh=f,source_url=g,source_locator=h)for a,b,c,d,e,f,g,h in flags])
rows=[]
for y,thermal,enterprise,bio,sustain,ren in [(2022,14265,104,73,8799,8726),(2023,18313,96,68,9665,9597),(2024,15247,105,78,10004,9927)]:
 rows.append(dict(issuer='SSE',fiscal_year_end=y,reported_thermal_gas_oil_gwh=thermal,whole_company_fossil_electricity_gwh='',unresolved_nonthermal_fossil_electricity_gwh='',constant_perimeter_thermal_gwh='',unresolved_output_decomposition_gwh='',whole_company_status='NA;nonthermal_fossil_component_unverified',enterprise_mixed_output_gwh=enterprise,biomass_excluded_gwh=bio,renewable_segment_plus_biomass_gwh=ren+bio,sustainability_renewable_total_gwh=sustain,renewable_cross_report_gap_gwh=ren+bio-sustain,source_references='boundary_additional_source_cells.csv;issuer_year_cells.csv',note='mixed_heat_other_minus_biomass_must_not_be_assumed_fossil_electricity'))
write('whole_company_boundary_status.csv',rows)
print('Boundary supplement written; all raw whole-company and constant-perimeter quantities remain NA.')
