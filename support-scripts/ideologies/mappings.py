from collections import defaultdict


law_group_to_law = {
    "lawgroup_governance_principles": {
        "law_monarchy": "M",
        "law_presidential_republic": "R",
        "law_parliamentary_republic": "R",
        "law_theocracy": "TH",
        "law_council_republic": "CR",
        # "law_chiefdom": "",
    },
    "lawgroup_distribution_of_power": {
        "law_autocracy": "AU",
        "law_technocracy": "T",
        "law_oligarchy": "O",
        "law_landed_voting": "L",
        "law_wealth_voting": "W",
        "law_census_voting": "CS",
        "law_universal_suffrage": "US",
        "law_anarchy": "A",
        "law_single_party_state": "SP",
        # "law_elder_council": "",
    },
    "lawgroup_citizenship": {
        "law_ethnostate": "ETH",
        "law_national_supremacy": "NAT",
        "law_racial_segregation": "SEG",
        "law_cultural_exclusion": "CUL",
        "law_multicultural": "MUL",
    },
    "lawgroup_church_and_state": {
        "law_state_religion": "SR",
        "law_freedom_of_conscience": "SE",
        "law_total_separation": "SE",
        "law_state_atheism": "SA",
    },
    "lawgroup_bureaucracy": {
        "law_hereditary_bureaucrats": "HE",
        "law_appointed_bureaucrats": "AP",
        "law_elected_bureaucrats": "EL",
    },
    "lawgroup_army_model": {
        "law_peasant_levies": "PL",
        "law_national_militia": "NM",
        "law_mass_conscription": "MC",
        "law_professional_army": "PRO",
    },
    "lawgroup_internal_security": {
        "law_no_home_affairs": "NO",
        "law_national_guard": "NG",
        "law_secret_police": "SP",
        "law_guaranteed_liberties": "GL",
    },
    "lawgroup_economic_system": {
        "law_traditionalism": "T",
        "law_interventionism": "I",
        "law_agrarianism": "AG",
        "law_industry_banned": "IB",
        "law_laissez_faire": "LF",
        "law_cooperative_ownership": "COO",
        "law_command_economy": "CE",
    },
    "lawgroup_trade_policy": {
        "law_free_trade": "FM",
        "law_protectionism": "P",
        "law_isolationism": "I",
        "law_mercantilism": "M",
    },
    "lawgroup_taxation": {
        "law_consumption_based_taxation": "CON",
        "law_land_based_taxation": "LAN",
        "law_per_capita_based_taxation": "CAP",
        "law_proportional_taxation": "PRO",
        "law_graduated_taxation": "GRA",
    },
    "lawgroup_land_reform": {
        "law_serfdom": "SER",
        "law_tenant_farmers": "TEN",
        "law_homesteading": "FRE",
        "law_commercialized_agriculture": "COM",
        "law_collectivized_agriculture": "COL",
    },
    "lawgroup_colonization": {
        "law_no_colonial_affairs": "NO",
        "law_colonial_resettlement": "SET",
        "law_colonial_exploitation": "EXP",
    },
    "lawgroup_policing": {
        "law_no_police": "NO",
        "law_local_police": "LP",
        "law_dedicated_police": "DP",
        "law_militarized_police": "MP",
    },
    "lawgroup_education_system": {
        "law_no_schools": "NO",
        "law_religious_schools": "CHA",
        "law_private_schools": "PRI",
        "law_public_schools": "PUB",
    },
    "lawgroup_health_system": {
        "law_no_health_system": "NO",
        "law_charitable_health_system": "CHA",
        "law_private_health_insurance": "PRI",
        "law_public_health_insurance": "PUB",
    },
    "lawgroup_free_speech": {
        "law_outlawed_dissent": "OD",
        "law_censorship": "CS",
        "law_right_of_assembly": "RA",
        "law_protected_speech": "PS",
    },
    "lawgroup_labor_rights": {
        "law_no_workers_rights": "NO",
        "law_regulatory_bodies": "REG",
        "law_worker_protections": "WP",
    },
    "lawgroup_childrens_rights": {
        "law_child_labor_allowed": "NO",
        "law_restricted_child_labor": "RES",
        "law_compulsory_primary_school": "PRI",
    },
    "lawgroup_rights_of_women": {
        "law_no_womens_rights": "LG",
        "law_women_own_property": "OP",
        "law_women_in_the_workplace": "WW",
        "law_womens_suffrage": "WS",
    },
    "lawgroup_welfare": {
        "law_no_social_security": "NO",
        "law_poor_laws": "POR",
        "law_wage_subsidies": "WS",
        "law_old_age_pension": "OLD",
    },
    "lawgroup_migration": {
        "law_no_migration_controls": "NC",
        "law_migration_controls": "LM",
        "law_closed_borders": "CB",
    },
    "lawgroup_slavery": {
        "law_slavery_banned": "BAN",
        "law_debt_slavery": "YES",
        "law_slave_trade": "YES",
        "law_legacy_slavery": "LEG",
    },
}

lawgroup_to_column_name = {
    "lawgroup_governance_principles": "Gov Principles",
    "lawgroup_distribution_of_power": "Dist of Power",
    "lawgroup_citizenship": "Citizenship",
    "lawgroup_church_and_state": "Church",
    "lawgroup_bureaucracy": "Bureaucracy",
    "lawgroup_army_model": "Army",
    "lawgroup_internal_security": "Security",
    "lawgroup_economic_system": "Economics",
    "lawgroup_trade_policy": "Trade",
    "lawgroup_land_reform": "Land",
    "lawgroup_taxation": "Taxation",
    "lawgroup_colonization": "Colonization",
    "lawgroup_policing": "Policing",
    "lawgroup_education_system": "Education",
    "lawgroup_health_system": "Health",
    "lawgroup_free_speech": "Speech",
    "lawgroup_labor_rights": "Labor Rights",
    "lawgroup_childrens_rights": "Children",
    "lawgroup_rights_of_women": "Women",
    "lawgroup_welfare": "Welfare",
    "lawgroup_migration": "Migration",
    "lawgroup_slavery": "Slavery",
}


level_to_word = {
    "++": "strongly_approve",
    "+": "approve",
    "0": "neutral",
    "-": "disapprove",
    "--": "strongly_disapprove",
}


column_name_to_lawgroup = {v: k for k, v in lawgroup_to_column_name.items()}
law_to_law_groups = {k: {} for k in law_group_to_law.keys()}

for lg, laws in law_group_to_law.items():
    law_shortcut_to_law_keys = defaultdict(list)
    for law, law_shortcut in laws.items():
        law_shortcut_to_law_keys[law_shortcut].append(law)
    for law_shortcut, law_keys in law_shortcut_to_law_keys.items():
        law_to_law_groups[lg] = law_shortcut_to_law_keys
