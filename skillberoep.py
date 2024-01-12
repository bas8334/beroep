import pandas as pd
import streamlit as st
from streamlit_searchbox import st_searchbox

beroepen = pd.read_csv("occupations_nl.csv")
beroepen['altLabels'] = beroepen['altLabels'].str.replace('\n', ', ')
##beroepen['conceptUri'][1]
#beroepen[['conceptUri','preferredLabel','altLabels']]
##beroepen

skillberoepen = pd.read_csv("occupationSkillRelations_nl.csv")
#skillberoepen[['occupationUri',	'relationType',	'skillType','skillUri']]

skill = pd.read_csv("skills_nl.csv")
#skill[['conceptUri','preferredLabel']]

Skillberoep_U_df = pd.merge(skillberoepen, beroepen, how='left', left_on='occupationUri', right_on='conceptUri')
Skillberoep_U_df = pd.merge(Skillberoep_U_df, skill, how='left', left_on='skillUri', right_on='conceptUri')
# Vervang 'occupationUri' met 'preferredLabel'
# combined_df['occupationUri'] = combined_df['preferredLabel']

# Voeg 'altLabels' toe
# combined_df = combined_df.drop(columns=['conceptUri', 'preferredLabel'])
Skillberoep_U_df = Skillberoep_U_df.drop(columns=['occupationUri', 'skillUri','conceptType_x', 
'conceptUri_x', 'iscoGroup', 'hiddenLabels_x', 'status_x', 'modifiedDate_x', 'regulatedProfessionNote', 'scopeNote_x',
'definition_x', 'inScheme_x', 'code', 'conceptType_y', 'conceptUri_y', 'skillType_y', 'reuseLevel', 'hiddenLabels_y',
'status_y', 'modifiedDate_y', 'scopeNote_y', 'definition_y', 'inScheme_y'])

Skillberoep_U_df = Skillberoep_U_df.rename(columns={
    'skillType_x': 'skillType',
    'preferredLabel_x': 'beroepnaam',
    'altLabels_x': 'alt_beroepnaam',
    'description_x': 'beschrijving_beroepnaam',
    'preferredLabel_y': 'skill',
    'altLabels_y': 'alt_skill',
    'description_y': 'beschrijving_skill'
})

#Skillberoep_U_df
unieke_beroepen_df = beroepen[['preferredLabel']].drop_duplicates()
unieke_beroepen_df
df = Skillberoep_U_df

# Functie voor de searchbox zoekfunctionaliteit
def zoek_beroep(searchterm: str):
    if searchterm:
        zoekterm_lower = searchterm.lower()
        gefilterde_beroepen = df['beroepnaam'].apply(lambda x: zoekterm_lower in x.lower() if pd.notna(x) else False)
        return df[gefilterde_beroepen]['beroepnaam'].drop_duplicates().tolist()
    else:
        return []
    
def bereken_skills(beroep, vergelijkings_skills):
    beroep_skills = set(df[df['beroepnaam'] == beroep]['skill'])
    overlappende = beroep_skills.intersection(vergelijkings_skills)
    niet_overlappende = beroep_skills.difference(vergelijkings_skills)
    return ' | '.join(overlappende), ' | '.join(niet_overlappende)

def bereken_top_10(gekozen_beroep, aantal_top):
    geselecteerde_beroep_skills = set(df[df['beroepnaam'] == gekozen_beroep]['skill'])
    
    def bereken_score(row):
        if row['skill'] in geselecteerde_beroep_skills:
            return 1 if row['relationType'] == 'essential' else 0.5
        return 0

    df['score'] = df.apply(bereken_score, axis=1)
    score_per_beroep = df.groupby('beroepnaam')['score'].sum()

    top_beroepen = score_per_beroep.sort_values(ascending=False).head(aantal_top)
    hoogste_score = top_beroepen.max()
    top_beroepen_percentage = top_beroepen.apply(lambda x: (x / hoogste_score) * 100)

    skills_info = top_beroepen.index.to_series().apply(lambda x: bereken_skills(x, geselecteerde_beroep_skills))
    skills_info_df = pd.DataFrame(skills_info.tolist(), index=top_beroepen.index, columns=['overlappende_skills', 'niet_overlappende_skills'])
    
    alt_beroepnaam = df.groupby('beroepnaam')['alt_beroepnaam'].first()

    top_beroepen_df = pd.DataFrame({
        'score': top_beroepen,
        'percentage': top_beroepen_percentage,
        'alt_beroepnaam': top_beroepen.index.map(alt_beroepnaam)
    }).join(skills_info_df)

    return top_beroepen_df

# Functie om de topberoepen te berekenen op basis van geselecteerde skills
def bereken_top_beroepen_op_basis_van_skills(geselecteerde_skills, aantal_top):
    df['score'] = df['skill'].apply(lambda x: 1 if x in geselecteerde_skills else 0)
    score_per_beroep = df.groupby('beroepnaam')['score'].sum()

    top_beroepen = score_per_beroep.sort_values(ascending=False).head(aantal_top)
    hoogste_score = top_beroepen.max()
    top_beroepen_percentage = top_beroepen.apply(lambda x: (x / hoogste_score) * 100)

    skills_info = top_beroepen.index.to_series().apply(lambda x: bereken_skills(x, set(geselecteerde_skills)))
    skills_info_df = pd.DataFrame(skills_info.tolist(), index=top_beroepen.index, columns=['overlappende_skills', 'niet_overlappende_skills'])

    alt_beroepnaam = df.groupby('beroepnaam')['alt_beroepnaam'].first()

    top_beroepen_skills_df = pd.DataFrame({
        'score': top_beroepen,
        'percentage': top_beroepen_percentage,
        'alt_beroepnaam': top_beroepen.index.map(alt_beroepnaam)
    }).join(skills_info_df)

    return top_beroepen_skills_df


if 'ingelogd' not in st.session_state:
    st.session_state['ingelogd'] = False

st.title("Inloggen")

# Alleen het inlogformulier tonen als de gebruiker niet is ingelogd
if not st.session_state['ingelogd']:
    inlognaam = st.text_input("Gebruikersnaam")
    inlogcode = st.text_input("Wachtwoord", type="password")

    if st.button("Inloggen"):
        if inlognaam == "stan" and inlogcode == "partners2024":
            st.session_state['ingelogd'] = True
            st.success("Succesvol ingelogd!")
        else:
            st.error("Onjuiste gebruikersnaam of wachtwoord")

# De rest van de app tonen als de gebruiker is ingelogd
if st.session_state['ingelogd']:
# Streamlit interface
    st.subheader('Beroepen en Skills Analyse')

# Module voor het zoeken van een beroep
    st.subheader("Zoek naar een specifiek beroep")
    gekozen_beroep = st_searchbox(
        search_function=zoek_beroep,
        placeholder="Zoek een beroep...",
        label="Kies een beroep",
        key="beroep_searchbox"
    )
    aantal_top = st.slider("Kies het aantal topberoepen voor zoekopdracht", 6, 50, 10)

    if gekozen_beroep and st.button('Toon Top Beroepen voor Zoekopdracht'):
        top_beroepen_resultaten = bereken_top_10(gekozen_beroep, aantal_top)
        st.write(top_beroepen_resultaten)

# Nieuwe module: Kies een beroep en selecteer skills met een searchbox
    st.subheader("Kies een beroep en selecteer skills")

# Searchbox om een beroep te selecteren
    gekozen_beroep_voor_skills = st_searchbox(
        search_function=zoek_beroep,
        placeholder="Zoek een beroep voor skills...",
        label="Selecteer een beroep",
        key="beroep_skill_searchbox"
    )

    if gekozen_beroep_voor_skills:
    # Toon de skills gerelateerd aan het gekozen beroep
        gerelateerde_skills = df[df['beroepnaam'] == gekozen_beroep_voor_skills]['skill'].unique()
        geselecteerde_skills = st.multiselect('Selecteer relevante skills', gerelateerde_skills)

    # Knop om de top beroepen te tonen op basis van geselecteerde skills
        aantal_top_skills = st.slider("Kies het aantal topberoepen voor skillselectie", 6, 50, 10)
        if st.button('Toon Top Beroepen op basis van Skills'):
            top_beroepen_skills_resultaten = bereken_top_beroepen_op_basis_van_skills(geselecteerde_skills, aantal_top_skills)
            st.write(top_beroepen_skills_resultaten)
