#!/usr/bin/env python3
"""
Générateur de diagrammes UML — Système MNL (Minoterie de Lubumbashi / Gécamines)

Produit des fichiers .drawio séparés, conformes aux conventions UML :
  - diagrammes/diagramme_classes_MNL.drawio
  - diagrammes/diagramme_cas_utilisation_MNL.drawio
  - diagrammes/diagramme_sequence_mouture_MNL.drawio
  - diagrammes/diagramme_activite_mouture_MNL.drawio

Usage : python3 generate_diagrammes_uml.py
"""
from __future__ import annotations

import html as H
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "diagrammes"

# ── Utilitaires XML draw.io ───────────────────────────────────────────────────

_id = [10]


def nid() -> str:
    i = _id[0]
    _id[0] += 1
    return str(i)


def reset_ids() -> None:
    _id[0] = 10


def esc(text: str) -> str:
    return H.escape(text, quote=True)


def write_drawio(
    path: Path,
    name: str,
    cells: list[str],
    page_width: int = 1654,
    page_height: int = 1169,
) -> None:
    inner = "\n".join(cells)
    model = (
        '<mxGraphModel dx="1800" dy="900" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{page_width}" pageHeight="{page_height}" math="0" shadow="0">'
        f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{inner}</root></mxGraphModel>'
    )
    xml = f'<mxfile host="Electron">\n<diagram id="d1" name="{esc(name)}">{model}</diagram>\n</mxfile>'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-8")
    print(f"  ✓ {path}")


def title(text: str, x: int = 20, y: int = 10, w: int = 1200) -> str:
    return (
        f'<mxCell id="{nid()}" value="{esc(text)}" '
        f'style="text;html=1;align=center;fontStyle=1;fontSize=14;strokeColor=none;fillColor=none;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="30" as="geometry"/></mxCell>'
    )


# ── Diagramme de classes (3 compartiments UML) ───────────────────────────────

HEADER = 30
ROW = 21
SEP = 7

REL_STYLES = {
    "association": "endArrow=open;endFill=0;startArrow=none;startFill=0;",
    "aggregation": "endArrow=diamondThin;endFill=0;startArrow=none;startFill=0;",
    "composition": "endArrow=diamondThin;endFill=1;startArrow=none;startFill=0;",
    "dependency": "endArrow=open;endFill=0;dashed=1;dashPattern=8 4;startArrow=none;startFill=0;",
    "one_to_one": "endArrow=ERone;endFill=0;startArrow=ERmandOne;startFill=0;",
    "one_to_many": "endArrow=ERmany;endFill=0;startArrow=ERmandOne;startFill=0;",
}


def uml_class(
    name: str,
    attrs: list[str],
    ops: list[str],
    x: int,
    y: int,
    w: int = 260,
    fill: str = "#FFFFFF",
    stroke: str = "#000000",
) -> tuple[str, list[str]]:
    """Classe UML : compartiment nom | attributs | opérations."""
    cid = nid()
    cells: list[str] = []
    h = HEADER + len(attrs) * ROW + SEP + len(ops) * ROW + 8
    cells.append(
        f'<mxCell id="{cid}" value="{esc(name)}" '
        f'style="swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;'
        f'startSize={HEADER};fillColor={fill};strokeColor={stroke};'
        f'fontSize=12;align=center;html=1;whiteSpace=wrap;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    ay = HEADER
    for attr in attrs:
        cells.append(
            f'<mxCell id="{nid()}" value="{esc(attr)}" '
            f'style="text;strokeColor=none;fillColor=none;align=left;'
            f'spacingLeft=8;fontSize=11;html=1;whiteSpace=wrap;" '
            f'vertex="1" parent="{cid}">'
            f'<mxGeometry x="0" y="{ay}" width="{w}" height="{ROW}" as="geometry"/></mxCell>'
        )
        ay += ROW
    cells.append(
        f'<mxCell id="{nid()}" value="" style="line;strokeColor=inherit;fillColor=none;" '
        f'vertex="1" parent="{cid}">'
        f'<mxGeometry x="0" y="{ay}" width="{w}" height="{SEP}" as="geometry"/></mxCell>'
    )
    ay += SEP
    for op in ops:
        cells.append(
            f'<mxCell id="{nid()}" value="{esc(op)}" '
            f'style="text;strokeColor=none;fillColor=none;align=left;'
            f'spacingLeft=8;fontSize=11;fontStyle=2;html=1;whiteSpace=wrap;" '
            f'vertex="1" parent="{cid}">'
            f'<mxGeometry x="0" y="{ay}" width="{w}" height="{ROW}" as="geometry"/></mxCell>'
        )
        ay += ROW
    return cid, cells


def uml_assoc(
    src: str,
    tgt: str,
    label: str = "",
    role_src: str = "",
    role_tgt: str = "",
    mult_src: str = "",
    mult_tgt: str = "",
    kind: str = "association",
) -> str:
    """Association UML avec rôle et multiplicité."""
    arrow = REL_STYLES.get(kind, REL_STYLES["association"])
    lbl = label
    if role_src or mult_src:
        lbl = f"{mult_src} {role_src}".strip()
    style = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;{arrow}"
        f"strokeColor=#333333;fontColor=#000000;fontSize=10;"
        f"labelBackgroundColor=#FFFFFF;align=center;"
    )
    edge_id = nid()
    parts = [
        f'<mxCell id="{edge_id}" value="{esc(lbl)}" style="{style}" '
        f'edge="1" source="{src}" target="{tgt}" parent="1">',
        f'<mxGeometry relative="1" as="geometry"/>',
    ]
    if mult_tgt or role_tgt:
        parts.insert(
            2,
            f'<mxCell id="{nid()}" value="{esc(f"{mult_tgt} {role_tgt}".strip())}" '
            f'style="edgeLabel;html=1;align=center;verticalAlign=middle;'
            f'resizable=0;points=[];fontSize=10;labelBackgroundColor=#FFFFFF;" '
            f'vertex="1" connectable="0" parent="{edge_id}">'
            f'<mxGeometry x="-0.2" y="1" relative="1" as="geometry">'
            f'<mxPoint as="offset"/></mxGeometry></mxCell>',
        )
    parts.append("</mxCell>")
    return "\n".join(parts)


def gen_classes() -> None:
    reset_ids()
    c: list[str] = []
    c.append(title("Diagramme de classes — Système MNL (notation UML)"))

    # ── Acteurs & entités métier ──────────────────────────────────────────────
    u, x = uml_class(
        "Utilisateur",
        [
            "- id : Integer {PK}",
            "- nom : String",
            "- prenom : String",
            "- email : String {unique}",
            "- motDePasse : String {hashed}",
            "- role : Role <<enumeration>>",
            "- actif : Boolean",
            "- dateCreation : DateTime",
        ],
        [
            "+ seConnecter() : Boolean",
            "+ seDeconnecter() : void",
            "+ changerMotDePasse(mdp: String) : void",
        ],
        40, 50, 270, "#DAE8FC", "#6C8EBF",
    )
    c += x

    cl, x = uml_class(
        "Client",
        [
            "- id : Integer {PK}",
            "- nom : String",
            "- prenom : String",
            "- telephone : String",
            "- adresse : String",
            "- email : String",
            "- dateEnregistrement : Date",
        ],
        [
            "+ passerCommande() : ContratMouture",
            "+ consulterHistoriqueRetrait() : List<BonRetrait>",
        ],
        360, 50, 260, "#DAE8FC", "#6C8EBF",
    )
    c += x

    cm, x = uml_class(
        "ContratMouture",
        [
            "- id : Integer {PK}",
            "- numeroContrat : String {unique}",
            "- dateContrat : Date",
            "- quantiteKg : Float",
            "- statut : StatutContrat <<enumeration>>",
            "- observations : String",
        ],
        [
            "+ genererNumero() : String",
            "+ validerContrat() : void",
            "+ annuler() : void",
        ],
        680, 50, 280, "#D5E8D4", "#82B366",
    )
    c += x

    br, x = uml_class(
        "BonRetrait",
        [
            "- id : Integer {PK}",
            "- numeroBon : String {unique}",
            "- dateRetrait : Date",
            "- quantiteSacs : Integer",
            "- factureReglee : Boolean",
        ],
        ["+ genererBon() : void", "+ imprimer() : PDF"],
        1020, 50, 260, "#FFF2CC", "#D6B656",
    )
    c += x

    rc, x = uml_class(
        "Reception",
        [
            "- id : Integer {PK}",
            "- numeroBon : String {unique}",
            "- dateReception : Date",
            "- poidsBrutKg : Float",
            "- poidsNetKg : Float",
            "- observations : String",
        ],
        [
            "+ genererBonReception() : void",
            "+ genererNumero() : String",
            "+ imprimer() : PDF",
        ],
        360, 380, 260, "#D5E8D4", "#82B366",
    )
    c += x

    pd, x = uml_class(
        "Production",
        [
            "- id : Integer {PK}",
            "- numeroProduction : String {unique}",
            "- dateDebut : Date",
            "- dateFin : Date",
            "- quantiteTraiteeKg : Float",
            "- quantiteFarineKg : Float",
            "- pertesKg : Float",
            "- statut : StatutProduction <<enumeration>>",
        ],
        [
            "+ lancerMouture() : void",
            "+ terminerMouture() : void",
            "+ rendement() : Float",
        ],
        680, 380, 280, "#D5E8D4", "#82B366",
    )
    c += x

    smp, x = uml_class(
        "StockMP",
        [
            "- id : Integer {PK}",
            "- quantiteDisponibleKg : Float",
            "- dateMaj : DateTime",
        ],
        ["+ mettreAJour(qte: Float) : void", "+ consulterStock() : Float"],
        40, 380, 260, "#F8CECC", "#B85450",
    )
    c += x

    ec, x = uml_class(
        "Echantillon",
        [
            "- id : Integer {PK}",
            "- numeroEchantillon : String {unique}",
            "- dateEnvoiLabo : Date",
            "- statut : StatutEchantillon <<enumeration>>",
        ],
        ["+ genererNumero() : String", "+ envoyerAuLabo() : void"],
        360, 720, 260, "#E1D5E7", "#9673A6",
    )
    c += x

    rl, x = uml_class(
        "ResultatLaboratoire",
        [
            "- id : Integer {PK}",
            "- dateAnalyse : Date",
            "- tauxHumidite : Float",
            "- tauxAcidite : Float",
            "- tauxMatiereGrasse : Float",
            "- conforme : Boolean",
            "- observations : String",
        ],
        [
            "+ encoderResultat() : void",
            "+ calculerConformite() : Boolean",
            "+ notifierMeunier() : void",
        ],
        680, 720, 280, "#E1D5E7", "#9673A6",
    )
    c += x

    pf, x = uml_class(
        "ProduitFini",
        [
            "- id : Integer {PK}",
            "- typeSac : TypeSac <<enumeration>>",
            "- nombreSacs : Integer",
            "- poidsTotalKg : Float",
            "- referenceLot : String",
            "- dateEnsachage : Date",
        ],
        ["+ genererStockage() : void", "+ genererReferenceLot() : String"],
        680, 1060, 280, "#D5E8D4", "#82B366",
    )
    c += x

    sf, x = uml_class(
        "StockFarine",
        [
            "- id : Integer {PK}",
            "- typeFarine : String",
            "- quantiteSacs : Integer",
            "- quantiteKg : Float",
            "- dateMaj : DateTime",
        ],
        ["+ mettreAJour(qte: Integer) : void", "+ consulterStock() : Map"],
        40, 720, 260, "#F8CECC", "#B85450",
    )
    c += x

    al, x = uml_class(
        "Alerte",
        [
            "- id : Integer {PK}",
            "- type : TypeAlerte <<enumeration>>",
            "- message : String",
            "- lu : Boolean",
            "- dateCreation : DateTime",
        ],
        ["+ marquerLu() : void"],
        1020, 380, 260, "#FFF2CC", "#D6B656",
    )
    c += x

    # ── Énumérations UML (stéréotype <<enumeration>>) ─────────────────────────
    enums = [
        ("Role", "ADMIN, COMPTABLE, MAGASINIER, LABORANTIN, MEUNIER", 40, 1060, 220),
        ("StatutContrat", "EN_ATTENTE, EN_COURS, TERMINE, ANNULE", 280, 1060, 240),
        ("TypeAlerte", "RESULTAT_LABO, LIVRAISON_PRETE, RETARD, ANOMALIE", 1020, 720, 260),
    ]
    for ename, values, ex, ey, ew in enums:
        eid = nid()
        c.append(
            f'<mxCell id="{eid}" value="&lt;&lt;enumeration&gt;&gt;&#xa;{esc(ename)}" '
            f'style="swimlane;fontStyle=1;startSize=30;fillColor=#F5F5F5;'
            f'strokeColor=#666666;fontSize=11;html=1;" vertex="1" parent="1">'
            f'<mxGeometry x="{ex}" y="{ey}" width="{ew}" height="90" as="geometry"/></mxCell>'
        )
        c.append(
            f'<mxCell id="{nid()}" value="{esc(values)}" '
            f'style="text;strokeColor=none;fillColor=none;align=left;spacingLeft=8;fontSize=10;" '
            f'vertex="1" parent="{eid}">'
            f'<mxGeometry x="0" y="30" width="{ew}" height="55" as="geometry"/></mxCell>'
        )

    # ── Associations UML (multiplicités aux extrémités) ───────────────────────
    c.append(uml_assoc(cl, cm, mult_src="1", mult_tgt="0..*", role_tgt="contrats", kind="one_to_many"))
    c.append(uml_assoc(cm, rc, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(cm, pd, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(cm, br, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(rc, smp, mult_src="1", mult_tgt="1..*", role_tgt="mouvements", kind="one_to_many"))
    c.append(uml_assoc(rc, ec, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(ec, rl, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(pd, pf, mult_src="1", mult_tgt="1..*", role_tgt="produitsFinis", kind="one_to_many"))
    c.append(uml_assoc(pf, sf, mult_src="1", mult_tgt="1..*", role_tgt="entreesStock", kind="one_to_many"))
    c.append(uml_assoc(u, cm, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, rc, mult_src="1", mult_tgt="0..*", role_tgt="magasinier", kind="association"))
    c.append(uml_assoc(u, ec, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, rl, mult_src="1", mult_tgt="0..*", role_tgt="laborantin", kind="association"))
    c.append(uml_assoc(u, pd, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, br, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, al, mult_src="1", mult_tgt="0..*", role_tgt="destinataire", kind="association"))
    c.append(uml_assoc(cl, br, mult_src="1", mult_tgt="0..*", role_tgt="bonsRetrait", kind="one_to_many"))

    write_drawio(OUT_DIR / "diagramme_classes_MNL.drawio", "Classes MNL", c)


# ── Diagramme de cas d'utilisation ──────────────────────────────────────────


def use_case(name: str, x: int, y: int, w: int = 200, h: int = 50) -> str:
    return (
        f'<mxCell id="{nid()}" value="{esc(name)}" '
        f'style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=11;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def actor(name: str, x: int, y: int) -> str:
    aid = nid()
    return aid, (
        f'<mxCell id="{aid}" value="{esc(name)}" '
        f'style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;'
        f'html=1;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;fontSize=11;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="40" height="80" as="geometry"/></mxCell>'
    )


def system_boundary(label: str, x: int, y: int, w: int, h: int) -> str:
    return (
        f'<mxCell id="{nid()}" value="{esc(label)}" '
        f'style="swimlane;startSize=30;fillColor=none;strokeColor=#000000;'
        f'fontStyle=1;fontSize=12;dashed=0;" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def link_actor_uc(actor_id: str, uc_id: str) -> str:
    return (
        f'<mxCell id="{nid()}" value="" style="endArrow=none;html=1;strokeColor=#333333;" '
        f'edge="1" source="{actor_id}" target="{uc_id}" parent="1">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>'
    )


def link_uc_uc(src: str, tgt: str, stereotype: str = "<<include>>") -> str:
    return (
        f'<mxCell id="{nid()}" value="{esc(stereotype)}" '
        f'style="endArrow=open;dashed=1;html=1;strokeColor=#333333;fontSize=10;" '
        f'edge="1" source="{src}" target="{tgt}" parent="1">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>'
    )


def gen_use_cases() -> None:
    reset_ids()
    c: list[str] = []
    c.append(title("Diagramme de cas d'utilisation — Système MNL"))

    # Frontière du système
    sys_id = nid()
    c.append(
        f'<mxCell id="{sys_id}" value="Système MNL" '
        f'style="swimlane;startSize=30;fillColor=#F9F9F9;strokeColor=#000000;'
        f'fontStyle=1;fontSize=13;" vertex="1" parent="1">'
        f'<mxGeometry x="200" y="60" width="900" height="900" as="geometry"/></mxCell>'
    )

    def uc(name: str, x: int, y: int) -> str:
        uid = nid()
        c.append(
            f'<mxCell id="{uid}" value="{esc(name)}" '
            f'style="ellipse;whiteSpace=wrap;html=1;fillColor=#DAE8FC;'
            f'strokeColor=#6C8EBF;fontSize=11;" vertex="1" parent="{sys_id}">'
            f'<mxGeometry x="{x}" y="{y}" width="210" height="55" as="geometry"/></mxCell>'
        )
        return uid

    # Cas d'utilisation par zone
    uc_auth = uc("S'authentifier", 340, 40)
    uc_gest_user = uc("Gérer les utilisateurs", 80, 140)
    uc_dashboard = uc("Consulter le tableau de bord", 560, 140)
    uc_client = uc("Enregistrer un client", 80, 260)
    uc_contrat = uc("Créer un contrat de mouture", 340, 260)
    uc_retrait = uc("Générer un bon de retrait", 600, 260)
    uc_reception = uc("Enregistrer une réception", 80, 400)
    uc_stock_mp = uc("Consulter le stock MP", 340, 400)
    uc_echantillon = uc("Envoyer un échantillon au labo", 600, 400)
    uc_resultat = uc("Encoder un résultat d'analyse", 80, 540)
    uc_mouture = uc("Lancer / terminer une mouture", 340, 540)
    uc_ensachage = uc("Enregistrer l'ensachage", 600, 540)
    uc_stock_far = uc("Consulter le stock farine", 80, 680)
    uc_alerte = uc("Consulter les alertes", 340, 680)
    uc_hist = uc("Consulter l'historique des retraits", 600, 680)
    uc_pdf_rec = uc("Imprimer bon de réception (PDF)", 200, 820)
    uc_pdf_ret = uc("Imprimer bon de retrait (PDF)", 500, 820)

    # Relations include
    c.append(link_uc_uc(uc_reception, uc_pdf_rec))
    c.append(link_uc_uc(uc_retrait, uc_pdf_ret))
    c.append(link_uc_uc(uc_contrat, uc_auth))
    c.append(link_uc_uc(uc_mouture, uc_resultat, "<<extend>>"))

    # Acteurs (hors frontière)
    actors_def = [
        ("Administrateur", 60, 200, [uc_gest_user, uc_dashboard, uc_auth]),
        ("Comptable", 60, 350, [uc_client, uc_contrat, uc_retrait, uc_pdf_ret, uc_auth]),
        ("Magasinier", 60, 500, [uc_reception, uc_stock_mp, uc_echantillon, uc_pdf_rec, uc_auth]),
        ("Laborantin", 1140, 500, [uc_resultat, uc_auth]),
        ("Meunier", 1140, 350, [uc_mouture, uc_ensachage, uc_stock_far, uc_alerte, uc_echantillon, uc_auth]),
        ("Client", 1140, 700, [uc_hist]),
    ]
    for aname, ax, ay, ucs in actors_def:
        aid, axml = actor(aname, ax, ay)
        c.append(axml)
        for u in ucs:
            c.append(link_actor_uc(aid, u))

    write_drawio(OUT_DIR / "diagramme_cas_utilisation_MNL.drawio", "Cas d'utilisation MNL", c)


# ── Diagramme de séquence ─────────────────────────────────────────────────────

def seq_participant_box(name: str, cx: int, y: int, w: int = 120) -> list[str]:
    """En-tête participant UML (rectangle) + ligne de vie pointillée."""
    x = cx - w // 2
    return [
        (
            f'<mxCell id="{nid()}" value="{esc(name)}" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor=#DAE8FC;'
            f'strokeColor=#6C8EBF;fontStyle=1;fontSize=12;align=center;" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="44" as="geometry"/></mxCell>'
        ),
        (
            f'<mxCell id="{nid()}" value="" style="endArrow=none;dashed=1;dashPattern=1 4;'
            f'html=1;strokeColor=#666666;strokeWidth=1;" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{cx}" y="{y + 44}" as="sourcePoint"/>'
            f'<mxPoint x="{cx}" y="1020" as="targetPoint"/>'
            f'</mxGeometry></mxCell>'
        ),
    ]


def seq_frame(label: str, x: int, y: int, w: int, h: int) -> str:
    """Cadre de phase pour regrouper visuellement les messages."""
    return (
        f'<mxCell id="{nid()}" value="{esc(label)}" '
        f'style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;'
        f'strokeColor=#999999;dashed=1;dashPattern=8 4;'
        f'verticalAlign=top;fontStyle=1;fontSize=11;align=left;spacingLeft=8;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def seq_message(x1: int, x2: int, y: int, label: str, is_return: bool = False) -> str:
    """Message horizontal à coordonnées fixes (évite le chevauchement)."""
    if is_return:
        style = (
            "html=1;verticalAlign=bottom;endArrow=open;endFill=0;"
            "dashed=1;dashPattern=8 4;rounded=0;strokeColor=#333333;"
            "fontSize=11;labelBackgroundColor=#FFFFFF;"
        )
    else:
        style = (
            "html=1;verticalAlign=bottom;endArrow=block;rounded=0;"
            "strokeColor=#333333;fontSize=11;labelBackgroundColor=#FFFFFF;"
        )
    return (
        f'<mxCell id="{nid()}" value="{esc(label)}" style="{style}" '
        f'edge="1" parent="1">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x1}" y="{y}" as="sourcePoint"/>'
        f'<mxPoint x="{x2}" y="{y}" as="targetPoint"/>'
        f'</mxGeometry></mxCell>'
    )


def gen_sequence() -> None:
    reset_ids()
    c: list[str] = []
    c.append(title("Diagramme de séquence — Flux complet de mouture", w=1100))

    # Centres des lignes de vie (espacement large)
    P = {
        "Client":     90,
        "Comptable":  270,
        "Magasinier": 450,
        "Système":    680,
        "Laborantin": 870,
        "Meunier":   1050,
    }

    for name, cx in P.items():
        w = 150 if name == "Système" else 120
        label = ":Système MNL" if name == "Système" else name
        c.extend(seq_participant_box(label, cx, 50, w))

    c.append(seq_frame("Phase 1 — Contrat de mouture", 30, 125, 1120, 115))
    c.append(seq_frame("Phase 2 — Réception & laboratoire", 30, 310, 1120, 200))
    c.append(seq_frame("Phase 3 — Production & retrait", 30, 580, 1120, 200))

    msgs: list[tuple[str, str, str, int, bool]] = [
        ("Client",     "Comptable",  "1 : demandeMouture()",                     160, False),
        ("Comptable",  "Système",    "2 : creerContrat(client, qteKg)",          185, False),
        ("Système",    "Comptable",  "3 : numeroContrat (CM-…)",                 210, True),
        ("Magasinier", "Système",    "4 : enregistrerReception(contrat, poids)", 340, False),
        ("Système",    "Magasinier", "5 : bonReception (BRC-…) + stockMP",       365, True),
        ("Magasinier", "Système",    "6 : envoyerEchantillon(reception)",         390, False),
        ("Laborantin", "Système",    "7 : encoderResultat(echantillon, tauxs)",  430, False),
        ("Système",    "Meunier",    "8 : alerte(resultatLabo, conforme?)",       465, True),
        ("Meunier",    "Système",    "9 : lancerMouture(contrat)",                610, False),
        ("Meunier",    "Système",    "10 : terminerMouture(qteFarine, sacs)",     645, False),
        ("Système",    "Meunier",    "11 : stockFarine + referenceLot",           680, True),
        ("Comptable",  "Système",    "12 : genererBonRetrait(contrat, paiement)", 720, False),
        ("Système",    "Client",     "13 : bonRetrait (BRT-…) PDF",               755, True),
    ]
    for src, tgt, lbl, y, ret in msgs:
        c.append(seq_message(P[src], P[tgt], y, lbl, ret))

    write_drawio(
        OUT_DIR / "diagramme_sequence_mouture_MNL.drawio",
        "Séquence mouture MNL",
        c,
        page_width=1200,
        page_height=1100,
    )


# ── Diagramme d'activité ──────────────────────────────────────────────────────

def activity_node(kind: str, label: str, x: int, y: int, w: int = 160, h: int = 50) -> str:
    styles = {
        "start": "ellipse;fillColor=#000000;strokeColor=#000000;html=1;",
        "end": "ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=3;html=1;",
        "action": "rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=11;",
        "decision": "rhombus;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;fontSize=11;",
        "fork": "line;strokeWidth=4;html=1;strokeColor=#000000;",
    }
    nid_val = nid()
    return nid_val, (
        f'<mxCell id="{nid_val}" value="{esc(label)}" style="{styles[kind]}" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def activity_edge(src: str, tgt: str, label: str = "") -> str:
    return (
        f'<mxCell id="{nid()}" value="{esc(label)}" '
        f'style="endArrow=block;html=1;strokeColor=#333333;fontSize=10;" '
        f'edge="1" source="{src}" target="{tgt}" parent="1">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>'
    )


def gen_activity() -> None:
    reset_ids()
    c: list[str] = []
    c.append(title("Diagramme d'activité — Processus de mouture MNL"))

    s, xml = activity_node("start", "", 310, 60, 30, 30)
    c.append(xml)

    a1, xml = activity_node("action", "Créer contrat de mouture\n(Comptable)", 260, 120, 200, 55)
    c.append(xml)
    a2, xml = activity_node("action", "Réceptionner le maïs\n(Magasinier)", 260, 210, 200, 55)
    c.append(xml)
    a3, xml = activity_node("action", "Mettre à jour Stock MP", 260, 300, 200, 50)
    c.append(xml)
    a4, xml = activity_node("action", "Envoyer échantillon\nau labo Likasi", 260, 380, 200, 55)
    c.append(xml)
    a5, xml = activity_node("action", "Analyser l'échantillon\n(Laborantin)", 260, 470, 200, 55)
    c.append(xml)
    d1, xml = activity_node("decision", "Maïs\nconforme ?", 285, 560, 150, 80)
    c.append(xml)
    a6, xml = activity_node("action", "Lancer la mouture\n(Meunier)", 80, 680, 180, 55)
    c.append(xml)
    a7, xml = activity_node("action", "Ensacher la farine\n(25 / 50 kg)", 80, 770, 180, 55)
    c.append(xml)
    a8, xml = activity_node("action", "Mettre à jour\nStock farine", 80, 860, 180, 50)
    c.append(xml)
    a9, xml = activity_node("action", "Générer bon de retrait\n(Comptable)", 80, 940, 180, 55)
    c.append(xml)
    a10, xml = activity_node("action", "Rejet / nouvel\néchantillon", 460, 680, 180, 55)
    c.append(xml)
    e, xml = activity_node("end", "", 135, 1040, 30, 30)
    c.append(xml)
    e2, xml = activity_node("end", "", 515, 780, 30, 30)
    c.append(xml)

    flow = [
        (s, a1, ""),
        (a1, a2, ""),
        (a2, a3, ""),
        (a3, a4, ""),
        (a4, a5, ""),
        (a5, d1, ""),
        (d1, a6, "[oui]"),
        (d1, a10, "[non]"),
        (a6, a7, ""),
        (a7, a8, ""),
        (a8, a9, ""),
        (a9, e, ""),
        (a10, e2, ""),
    ]
    for src, tgt, lbl in flow:
        c.append(activity_edge(src, tgt, lbl))

    # Swimlanes (partition UML)
    lanes = [
        ("Comptable", 40, 100, 220, 920, "#E8F5E9"),
        ("Magasinier", 270, 100, 220, 320, "#E3F2FD"),
        ("Laboratoire", 270, 430, 220, 220, "#F3E5F5"),
        ("Meunier", 40, 650, 220, 280, "#FFF8E1"),
    ]
    for lname, lx, ly, lw, lh, color in lanes:
        c.insert(
            1,
            (
                f'<mxCell id="{nid()}" value="{esc(lname)}" '
                f'style="swimlane;startSize=25;fillColor={color};strokeColor=#999999;'
                f'fontStyle=1;fontSize=11;horizontal=0;" vertex="1" parent="1">'
                f'<mxGeometry x="{lx}" y="{ly}" width="{lw}" height="{lh}" as="geometry"/></mxCell>'
            ),
        )

    write_drawio(OUT_DIR / "diagramme_activite_mouture_MNL.drawio", "Activité mouture MNL", c)


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main() -> None:
    print("Génération des diagrammes UML MNL…")
    gen_classes()
    gen_use_cases()
    gen_sequence()
    gen_activity()
    print(f"\nTerminé — {OUT_DIR}/")


if __name__ == "__main__":
    main()
