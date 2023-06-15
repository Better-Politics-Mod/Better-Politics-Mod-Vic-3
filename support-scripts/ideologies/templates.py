class TEMPALTES:
    ideology_law_approval = "\t\t{law_key} = {approval_level}"

    ideology_law = """
    {law_group_key} = {{
{law_approvals}
    }}
    """

    ideology = """
ideology_{category}_{ideology_key} = {{
    icon = "gfx/interface/icons/ideology_icons/{category}_ideology/{ideology_key}.dds"
    {laws}
}}
    """
