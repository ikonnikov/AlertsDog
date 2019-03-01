# -*- coding: utf-8 -*-

from utils import Sinks as sinks


def fill_task_broker(task_broker):
    morning_run = sinks.TaskSinkChain(chain_id=u'mr1', name=u'Morning Run (MSK)', start=u'08:05:00', end=u'08:45:00')
    morning_run.push({'name': u'Update Bloomberg Static Data', 'phrase': u'{cf2.1, PROD}', 'lag_s': 200, 'duration_s': 200})
    morning_run.push({'name': u'Update MICEX Fund', 'phrase': u'{cf3.1, PROD}', 'lag_s': 700, 'duration_s': 420})
    morning_run.push({'name': u'Update Liquidity Local', 'phrase': u'{cf4.1, PROD}', 'lag_s': 700, 'duration_s': 60})
    morning_run.push({'name': u'Update Liquidity Foreign', 'phrase': u'{cf5.1, PROD}', 'lag_s': 1200, 'duration_s': 430})
    morning_run.push({'name': u'Update MICEX Index', 'phrase': u'{cf6.1, PROD}', 'lag_s': 1200, 'duration_s': 20})
    morning_run.push({'name': u'Update RTS Index', 'phrase': u'{cf7.1, PROD}', 'lag_s': 1200, 'duration_s': 10})
    morning_run.push({'name': u'Update MSCI Russia', 'phrase': u'{cf9.1, PROD}', 'lag_s': 1200, 'duration_s': 15})
    morning_run.push({'name': u'Update CBonds Calls', 'phrase': u'{cf10.1, PROD}', 'lag_s': 1250, 'duration_s': 20})
    morning_run.push({'name': u'Update CBonds Sinks', 'phrase': u'{cf13.1, PROD}', 'lag_s': 1700, 'duration_s': 300})
    morning_run.push({'name': u'Update FACTOR', 'phrase': u'{cf14.1, PROD}', 'lag_s': 1750, 'duration_s': 70})
    morning_run.push({'name': u'Update FXRates', 'phrase': u'{cf15.1, PROD}', 'lag_s': 1750, 'duration_s': 5})
    morning_run.push({'name': u'Fix Maturity Date', 'phrase': u'{cf16.1, PROD}', 'lag_s': 1750, 'duration_s': 5})
    morning_run.push({'name': u'Update Issuer Affiliates Company from PRIME', 'phrase': u'{cf18.1, PROD}', 'lag_s': 1850, 'duration_s': 100})
    morning_run.push({'name': u'Update Issuer Capitalization', 'phrase': u'{cf19.1, PROD}', 'lag_s': 1850, 'duration_s': 15})
    morning_run.push({'name': u'System Diff Report', 'phrase': u'{cf20.1, PROD}', 'lag_s': 1850, 'duration_s': 5})
    morning_run.push({'name': u'Update JPM Index', 'phrase': u'{cf21.1, PROD}', 'lag_s': 1850, 'duration_s': 5})
    morning_run.push({'name': u'Update Coupon Data', 'phrase': u'{cf22.1, PROD}', 'lag_s': 1950, 'duration_s': 120})
    morning_run.push({'name': u'Update CBonds Coupon Reset', 'phrase': u'{cf23.1, PROD}', 'lag_s': 2200, 'duration_s': 220})
    morning_run.push({'name': u'Issuers Duplicates', 'phrase': u'{cf24.1, PROD}', 'lag_s': 2200, 'duration_s': 5})
    morning_run.push({'name': u'Structured notes quote check up', 'phrase': u'{cf25.1, PROD}', 'lag_s': 2200, 'duration_s': 10})
    morning_run.push({'name': u'CRIMS Security Reference Corruption Check', 'phrase': u'{cf26.1, PROD}', 'lag_s': 2200, 'duration_s': 10})
    morning_run.push({'name': u'Update Security Lombard List', 'phrase': u'{cf49.1, PROD}', 'lag_s': 2250, 'duration_s': 40})
    morning_run.push({'name': u'Update Security Guarantors', 'phrase': u'{cf50.1, PROD}', 'lag_s': 2300, 'duration_s': 80})
    morning_run.push({'name': u'Update Unit Trust Constituents', 'phrase': u'{cf51.1, PROD}', 'lag_s': 2350, 'duration_s': 25})
    morning_run.push({'name': u'MorningRun finished', 'phrase': u'{cf1, PROD}', 'lag_s': 2400, 'duration_s': 5})
    task_broker.append_sink(morning_run)

    trading_open_run = sinks.TaskSinkChain(chain_id=u'tor1', name=u'Trading Open Run (MSK)', start=u'08:10:00', end=u'08:20:00')
    trading_open_run.push({'name': u'Delete BDR positions', 'phrase': u'{cf56.55, PROD}', 'lag_s': 360, 'duration_s': 350})
    trading_open_run.push({'name': u'Create Technical SOD Positions', 'phrase': u'{cf57.55, PROD}', 'lag_s': 360, 'duration_s': 5})
    trading_open_run.push({'name': u'Update Avan Deposits', 'phrase': u'{cf58.55, PROD}', 'lag_s': 430, 'duration_s': 90})
    trading_open_run.push({'name': u'Update Deposits', 'phrase': u'{cf59.55, PROD}', 'lag_s': 430, 'duration_s': 5})
    trading_open_run.push({'name': u'Update PIF Total Assets', 'phrase': u'{cf60.55, PROD}', 'lag_s': 450, 'duration_s': 45})
    trading_open_run.push({'name': u'CRIMS Quality check', 'phrase': u'{cf33.55, PROD}', 'lag_s': 500, 'duration_s': 10})
    task_broker.append_sink(trading_open_run)

    crims_pos = sinks.TaskSinkChain(chain_id=u'crims_pos_1', name=u'Open CRIMS Day (MSK)', start=u'08:20:00', end=u'09:45:00')
    crims_pos.push({'name': u'Update CRIMS price', 'phrase': u'{mf54, PROD}', 'lag_s': 3415, 'duration_s': 3415})
    crims_pos.push({'name': u'Update CRIMS position', 'phrase': u'{mf53, PROD}', 'lag_s': 4270, 'duration_s': 850})
    crims_pos.push({'name': u'REPRICE (morning)', 'phrase': u'REPRICE EOD log (morning). {PROD}', 'lag_s': 4700, 'duration_s': 450})
    crims_pos.push({'name': u'COMPLIANCE (morning). {PROD}', 'phrase': u'COMPLIANCE EOD log (morning). {PROD}', 'lag_s': 5050, 'duration_s': 350})
    task_broker.append_sink(crims_pos)

    rates_data = sinks.TaskSinkGroup(group_id=u'rates_data_1', name=u'RATES data (currency)')
    rates_data.push({'name': u'RATES data (currency 07:00)', 'phrase': u'{if68, PROD}', 'start': u'07:00:00', 'duration_s': 120})
    rates_data.push({'name': u'RATES data (currency 15:00)', 'phrase': u'{if73, PROD}', 'start': u'15:00:00', 'duration_s': 120})
    task_broker.append_sink(rates_data)

    prime_data = sinks.TaskSinkIndividual({'id': u'prime_data_1', 'name': u'PRIME data loader', 'phrase': u'{if69, PROD}', 'start': u'08:05:00', 'duration_s': 20 * 60})
    task_broker.append_sink(prime_data)

    rates_du = sinks.TaskSinkIndividual({'id': u'rates_du_1', 'name': u'Котировки ДУ', 'phrase': u'{r12.1, ib: PROD_AVC_DU}', 'start': u'09:00:00', 'duration_s': 120})
    task_broker.append_sink(rates_du)

    rates_pif = sinks.TaskSinkIndividual({'id': u'rates_pif_1', 'name': u'Котировки ПИФ', 'phrase': u'{r49, ib: PROD_AVC_PIF}', 'start': u'07:58:00', 'duration_s': 180})
    task_broker.append_sink(rates_pif)

    rates_mo = sinks.TaskSinkIndividual({'id': u'rates_mo_1', 'name': u'Котировки МО', 'phrase': u'{r14.1, ib: PROD_AVC_MO}', 'start': u'09:00:00', 'duration_s': 180})
    task_broker.append_sink(rates_mo)

    rates_fin = sinks.TaskSinkIndividual({'id': u'rates_fin_1', 'name': u'Котировки ФИН', 'phrase': u'{r82, ib: PROD_AVC_FIN20}', 'start': u'08:50:00', 'duration_s': 4 * 60})
    task_broker.append_sink(rates_fin)

    rating_du = sinks.TaskSinkGroup(group_id=u'rating_du_1', name=u'Рейтинги ДУ')
    rating_du.push({'name': u'Рейтинги ДУ (ин. р.а.)', 'phrase': u'{r69.0, ib: PROD_AVC_DU}', 'start': u'12:15:00', 'duration_s': 120})
    rating_du.push({'name': u'Рейтинги ДУ (рос. р.а.)', 'phrase': u'{r69.1, ib: PROD_AVC_DU}', 'start': u'12:30:00', 'duration_s': 120})
    task_broker.append_sink(rating_du)

    rating_pif = sinks.TaskSinkIndividual({'id': u'rating_pif_1', 'name': u'Рейтинги ПИФ', 'phrase': u'{r59, ib: PROD_AVC_PIF}', 'start': u'11:00:00', 'duration_s': 260})
    task_broker.append_sink(rating_pif)

    rating_mo = sinks.TaskSinkGroup(group_id=u'rating_mo_1', name=u'Рейтинги МО')
    rating_mo.push({'name': u'Загрузка из Rates', 'phrase': u'{r79, ib: PROD_AVC_MO}', 'start': u'08:50:00', 'duration_s': 120})
    rating_mo.push({'name': u'Выгрузка в CRIMS', 'phrase': u'{r77, ib: PROD_AVC_MO}', 'start': u'09:00:00', 'duration_s': 4 * 60})
    task_broker.append_sink(rating_mo)

    assets_du = sinks.TaskSinkIndividual({'id': u'assets_du_1', 'name': u'Активы ДУ', 'phrase': u'{r84, ib: PROD_AVC_DU}', 'start': u'03:15:00', 'duration_s': 120})
    task_broker.append_sink(assets_du)

    assets_pif = sinks.TaskSinkIndividual({'id': u'assets_pif_1', 'name': u'Активы ПИФ', 'phrase': u'{r83, ib: PROD_AVC_PIF}', 'start': u'03:00:00', 'duration_s': 120})
    task_broker.append_sink(assets_pif)

    assets_mo = sinks.TaskSinkIndividual({'id': u'assets_mo_1', 'name': u'Активы МО', 'phrase': u'{r1, ib: PROD_AVC_MO}', 'start': u'03:00:00', 'duration_s': 20 * 60})
    task_broker.append_sink(assets_mo)

    currencies_du = sinks.TaskSinkGroup(group_id=u'currencies_du_1', name=u'Валюты ДУ')
    currencies_du.push({'name': u'Валюты ДУ (09:00)', 'phrase': u'{r9, ib: PROD_AVC_DU}', 'start': u'09:00:00', 'duration_s': 120})
    currencies_du.push({'name': u'Валюты ДУ (16:00)', 'phrase': u'{r89, ib: PROD_AVC_DU}', 'start': u'16:00:00', 'duration_s': 120})
    task_broker.append_sink(currencies_du)

    currencies_pif = sinks.TaskSinkIndividual({'id': u'currencies_pif_1', 'name': u'Валюты ПИФ', 'phrase': u'{r47, ib: PROD_AVC_PIF}', 'start': u'07:45:00', 'duration_s': 120})
    task_broker.append_sink(currencies_pif)

    currencies_mo = sinks.TaskSinkIndividual({'id': u'currencies_mo_1', 'name': u'Валюты МО', 'phrase': u'{r8.1, ib: PROD_AVC_MO}', 'start': u'09:00:00', 'duration_s': 120})
    task_broker.append_sink(currencies_mo)

    currencies_fin = sinks.TaskSinkIndividual({'id': u'currencies_fin_1', 'name': u'Валюты ФИН', 'phrase': u'{r86, ib: PROD_AVC_FIN20}', 'start': u'08:40:00', 'duration_s': 120})
    task_broker.append_sink(currencies_fin)

    curve_mo = sinks.TaskSinkIndividual({'id': u'curve_mo_1', 'name': u'MOEX G-curve', 'phrase': u'{r16, ib: PROD_AVC_MO}', 'start': u'10:00:00', 'duration_s': 120})
    task_broker.append_sink(curve_mo)

    indexes_pif = sinks.TaskSinkIndividual({'id': u'indexes_pif_1', 'name': u'Индексы ПИФ', 'phrase': u'{r46, ib: PROD_AVC_PIF}', 'start': u'07:10:00', 'duration_s': 120})
    task_broker.append_sink(indexes_pif)

    indexes_mo = sinks.TaskSinkIndividual({'id': u'indexes_mo_1', 'name': u'Индексы МО', 'phrase': u'{r7.1, ib: PROD_AVC_MO}', 'start': u'09:10:00', 'duration_s': 120})
    task_broker.append_sink(indexes_mo)

    # todo: для внесессионного контроля
    # risk_control_du = sinks.TaskSinkIndividual({'id': u'risk_control_du_1', 'name': u'Repo Risk control ДУ', 'phrase': u'{r32, ib: PROD_AVC_DU}', 'start': u'21:20:00', 'duration_s': 120})
    # task_broker.append_sink(risk_control_du)
    # todo: для внесессионного контроля

    deals_pif = sinks.TaskSinkGroup(group_id=u'deals_pif_1', name=u'Сделки ПИФ')
    deals_pif.push({'name': u'Сделки ПИФ бирж. (13:00)', 'phrase': u'{r51.1, ib: PROD_AVC_PIF}', 'start': u'13:00:00', 'duration_s': 4 * 60})
    deals_pif.push({'name': u'Сделки ПИФ бирж. (18:00)', 'phrase': u'{r51.1, ib: PROD_AVC_PIF}', 'start': u'18:00:00', 'duration_s': 6 * 60})
    # deals_pif.push({'name': u'Сделки ПИФ бирж. (19:20)', 'phrase': u'{r51.1, ib: PROD_AVC_PIF}', 'start': u'19:20:00', 'duration_s': 4 * 60})
    # deals_pif.push({'name': u'Сделки ПИФ бирж. (22:30)', 'phrase': u'{r51.1, ib: PROD_AVC_PIF}', 'start': u'22:30:00', 'duration_s': 4 * 60})
    # deals_pif.push({'name': u'Сделки ПИФ внебирж. (21:00)', 'phrase': u'{r51.2, ib: PROD_AVC_PIF}', 'start': u'21:00:00', 'duration_s': 2 * 60})
    task_broker.append_sink(deals_pif)
