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
CLASS_GAP = 55      # espace vertical entre deux classes
PACKAGE_PAD = 35    # marge intérieure des packages
PACKAGE_GAP = 45    # espace entre packages


def class_height(attrs: list[str], ops: list[str]) -> int:
    return HEADER + len(attrs) * ROW + SEP + len(ops) * ROW + 8


def uml_package(label: str, x: int, y: int, w: int, h: int) -> str:
    """Cadre de package UML (groupe logique)."""
    pid = nid()
    return (
        f'<mxCell id="{pid}" value="{esc(label)}" '
        f'style="shape=folder;fontStyle=1;spacingTop=12;tabWidth=120;tabHeight=22;'
        f'fillColor=none;strokeColor=#999999;dashed=1;dashPattern=6 4;'
        f'fontSize=12;html=1;whiteSpace=wrap;" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def stack_classes(
    specs: list[tuple],
    x: int,
    y: int,
    w: int,
) -> tuple[list[tuple[str, list[str]]], int]:
    """Empile des classes verticalement ; retourne [(id, cells), …] et hauteur totale."""
    placed: list[tuple[str, list[str]]] = []
    cy = y
    for spec in specs:
        name, attrs, ops, fill, stroke = spec
        cid, cells = uml_class(name, attrs, ops, x, cy, w, fill, stroke)
        placed.append((cid, cells))
        cy += class_height(attrs, ops) + CLASS_GAP
    total_h = cy - y - CLASS_GAP
    return placed, total_h

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
    c.append(title("Diagramme de classes — Système MNL (notation UML)", x=40, w=1600))

    W = 270

    # ── Définitions des classes (nom, attributs, opérations, fill, stroke) ───
    BLUE = ("#DAE8FC", "#6C8EBF")
    GREEN = ("#D5E8D4", "#82B366")
    RED = ("#F8CECC", "#B85450")
    PURPLE = ("#E1D5E7", "#9673A6")
    YELLOW = ("#FFF2CC", "#D6B656")

    utilisateur = (
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
        ["+ seConnecter() : Boolean", "+ seDeconnecter() : void",
         "+ changerMotDePasse(mdp: String) : void"],
        *BLUE,
    )
    client = (
        "Client",
        [
            "- id : Integer {PK}", "- nom : String", "- prenom : String",
            "- telephone : String", "- adresse : String", "- email : String",
            "- dateEnregistrement : Date",
        ],
        ["+ passerCommande() : Commande",
         "+ consulterHistoriqueRetrait() : List<BonRetrait>"],
        *BLUE,
    )
    commande = (
        "Commande",
        [
            "- id : Integer {PK}", "- numeroCommande : String {unique}",
            "- dateCommande : Date", "- quantiteKg : Float",
            "- statut : StatutCommande <<enumeration>>",
            "- observations : String",
        ],
        ["+ genererNumero() : String", "+ valider() : ContratMouture",
         "+ annuler() : void"],
        *BLUE,
    )
    contrat = (
        "ContratMouture",
        [
            "- id : Integer {PK}", "- numeroContrat : String {unique}",
            "- dateContrat : Date", "- quantiteKg : Float",
            "- statut : StatutContrat <<enumeration>>",
            "- observations : String",
        ],
        ["+ genererNumero() : String", "+ validerContrat() : void",
         "+ annuler() : void"],
        *GREEN,
    )
    bon_retrait = (
        "BonRetrait",
        [
            "- id : Integer {PK}", "- numeroBon : String {unique}",
            "- dateRetrait : Date", "- quantiteSacs : Integer",
            "- factureReglee : Boolean",
        ],
        ["+ genererBon() : void", "+ imprimer() : PDF"],
        *YELLOW,
    )
    reception = (
        "Reception",
        [
            "- id : Integer {PK}", "- numeroBon : String {unique}",
            "- dateReception : Date", "- poidsBrutKg : Float",
            "- poidsNetKg : Float", "- observations : String",
        ],
        ["+ genererBonReception() : void", "+ genererNumero() : String",
         "+ imprimer() : PDF"],
        *GREEN,
    )
    stock_mp = (
        "StockMP",
        ["- id : Integer {PK}", "- quantiteDisponibleKg : Float",
         "- dateMaj : DateTime"],
        ["+ mettreAJour(qte: Float) : void", "+ consulterStock() : Float"],
        *RED,
    )
    echantillon = (
        "Echantillon",
        [
            "- id : Integer {PK}", "- numeroEchantillon : String {unique}",
            "- dateEnvoiLabo : Date",
            "- statut : StatutEchantillon <<enumeration>>",
        ],
        ["+ genererNumero() : String", "+ envoyerAuLabo() : void"],
        *PURPLE,
    )
    resultat = (
        "ResultatLaboratoire",
        [
            "- id : Integer {PK}", "- dateAnalyse : Date",
            "- tauxHumidite : Float", "- tauxAcidite : Float",
            "- tauxMatiereGrasse : Float", "- conforme : Boolean",
            "- observations : String",
        ],
        ["+ encoderResultat() : void", "+ calculerConformite() : Boolean",
         "+ notifierMeunier() : void"],
        *PURPLE,
    )
    production = (
        "Production",
        [
            "- id : Integer {PK}", "- numeroProduction : String {unique}",
            "- dateDebut : Date", "- dateFin : Date",
            "- quantiteTraiteeKg : Float", "- quantiteFarineKg : Float",
            "- pertesKg : Float", "- statut : StatutProduction <<enumeration>>",
        ],
        ["+ lancerMouture() : void", "+ terminerMouture() : void",
         "+ rendement() : Float"],
        *GREEN,
    )
    produit_fini = (
        "ProduitFini",
        [
            "- id : Integer {PK}", "- typeSac : TypeSac <<enumeration>>",
            "- nombreSacs : Integer", "- poidsTotalKg : Float",
            "- referenceLot : String", "- dateEnsachage : Date",
        ],
        ["+ genererStockage() : void", "+ genererReferenceLot() : String"],
        *GREEN,
    )
    stock_farine = (
        "StockFarine",
        [
            "- id : Integer {PK}", "- typeFarine : String",
            "- quantiteSacs : Integer", "- quantiteKg : Float",
            "- dateMaj : DateTime",
        ],
        ["+ mettreAJour(qte: Integer) : void", "+ consulterStock() : Map"],
        *RED,
    )
    alerte = (
        "Alerte",
        [
            "- id : Integer {PK}", "- type : TypeAlerte <<enumeration>>",
            "- message : String", "- lu : Boolean", "- dateCreation : DateTime",
        ],
        ["+ marquerLu() : void"],
        *YELLOW,
    )

    # ── Disposition par packages (flux gauche → droite) ───────────────────────
    Y0 = 55

    # Colonne gauche : sécurité
    pkg_sec_x, pkg_sec_y = 40, Y0
    pkg_sec_w = W + 2 * PACKAGE_PAD
    sec_inner_x = pkg_sec_x + PACKAGE_PAD
    sec_inner_y = pkg_sec_y + PACKAGE_PAD + 18
    sec_items, sec_h = stack_classes([utilisateur, alerte], sec_inner_x, sec_inner_y, W)
    pkg_sec_h = sec_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» accounts / facturation", pkg_sec_x, pkg_sec_y, pkg_sec_w, pkg_sec_h))
    for _, cells in sec_items:
        c += cells
    u, _ = sec_items[0]
    al, _ = sec_items[1]

    # Package commercial — ligne horizontale
    pkg_com_x = pkg_sec_x + pkg_sec_w + PACKAGE_GAP
    pkg_com_y = Y0
    com_specs = [client, commande, contrat, bon_retrait]
    com_inner_y = pkg_com_y + PACKAGE_PAD + 18
    com_inner_x = pkg_com_x + PACKAGE_PAD
    com_gap_x = 50
    com_ids: list[str] = []
    com_cells: list[str] = []
    cx = com_inner_x
    max_com_h = 0
    for spec in com_specs:
        name, attrs, ops, fill, stroke = spec
        cid, cells = uml_class(name, attrs, ops, cx, com_inner_y, W, fill, stroke)
        com_ids.append(cid)
        com_cells += cells
        h = class_height(attrs, ops)
        max_com_h = max(max_com_h, h)
        cx += W + com_gap_x
    cl, co, cm, br = com_ids
    pkg_com_w = cx - com_inner_x + PACKAGE_PAD - com_gap_x
    pkg_com_h = max_com_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» clients / contrats / facturation", pkg_com_x, pkg_com_y, pkg_com_w, pkg_com_h))
    c += com_cells

    # Ligne opérations : magasin | laboratoire | production
    pkg_ops_y = pkg_com_y + pkg_com_h + PACKAGE_GAP
    col_w = W + 2 * PACKAGE_PAD
    col_gap = PACKAGE_GAP

    # Magasin
    mag_x = 40
    mag_inner_x = mag_x + PACKAGE_PAD
    mag_inner_y = pkg_ops_y + PACKAGE_PAD + 18
    mag_items, mag_h = stack_classes([reception, stock_mp], mag_inner_x, mag_inner_y, W)
    mag_pkg_h = mag_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» magasin", mag_x, pkg_ops_y, col_w, mag_pkg_h))
    for _, cells in mag_items:
        c += cells
    rc, smp = mag_items[0][0], mag_items[1][0]

    # Laboratoire
    lab_x = mag_x + col_w + col_gap
    lab_inner_x = lab_x + PACKAGE_PAD
    lab_items, lab_h = stack_classes([echantillon, resultat], lab_inner_x, mag_inner_y, W)
    lab_pkg_h = mag_h + 2 * PACKAGE_PAD + 18  # même hauteur visuelle
    lab_pkg_h = max(mag_pkg_h, lab_h + 2 * PACKAGE_PAD + 18)
    c.append(uml_package("«app» laboratoire", lab_x, pkg_ops_y, col_w, lab_pkg_h))
    for _, cells in lab_items:
        c += cells
    ec, rl = lab_items[0][0], lab_items[1][0]

    # Production
    prod_x = lab_x + col_w + col_gap
    prod_inner_x = prod_x + PACKAGE_PAD
    prod_items, prod_h = stack_classes(
        [production, produit_fini, stock_farine], prod_inner_x, mag_inner_y, W,
    )
    prod_pkg_h = prod_h + 2 * PACKAGE_PAD + 18
    prod_pkg_h = max(lab_pkg_h, prod_pkg_h)
    c.append(uml_package("«app» production", prod_x, pkg_ops_y, col_w, prod_pkg_h))
    for _, cells in prod_items:
        c += cells
    pd, pf, sf = prod_items[0][0], prod_items[1][0], prod_items[2][0]

    # Harmoniser hauteur des 3 packages opérations
    ops_row_h = max(mag_pkg_h, lab_pkg_h, prod_pkg_h)

    # Énumérations — bandeau bas
    enum_y = pkg_ops_y + ops_row_h + PACKAGE_GAP
    enum_gap = 35
    enum_x = 40
    enums = [
        ("Role", "ADMIN, COMPTABLE, MAGASINIER, LABORANTIN, MEUNIER", 240),
        ("StatutCommande", "EN_ATTENTE, VALIDEE, REFUSEE, ANNULEE", 280),
        ("StatutContrat", "EN_ATTENTE, EN_COURS, TERMINE, ANNULE", 260),
        ("TypeAlerte", "RESULTAT_LABO, LIVRAISON_PRETE, RETARD, ANOMALIE", 280),
    ]
    enum_total_w = sum(ew for _, _, ew in enums) + enum_gap * (len(enums) - 1)
    c.append(uml_package("Types énumérés", 40, enum_y, enum_total_w + 2 * PACKAGE_PAD, 130))
    ex = 40 + PACKAGE_PAD
    ey = enum_y + PACKAGE_PAD + 20
    for ename, values, ew in enums:
        eid = nid()
        c.append(
            f'<mxCell id="{eid}" value="&lt;&lt;enumeration&gt;&gt;&#xa;{esc(ename)}" '
            f'style="swimlane;fontStyle=1;startSize=30;fillColor=#F5F5F5;'
            f'strokeColor=#666666;fontSize=11;html=1;" vertex="1" parent="1">'
            f'<mxGeometry x="{ex}" y="{ey}" width="{ew}" height="85" as="geometry"/></mxCell>'
        )
        c.append(
            f'<mxCell id="{nid()}" value="{esc(values)}" '
            f'style="text;strokeColor=none;fillColor=none;align=left;spacingLeft=8;fontSize=10;" '
            f'vertex="1" parent="{eid}">'
            f'<mxGeometry x="0" y="30" width="{ew}" height="50" as="geometry"/></mxCell>'
        )
        ex += ew + enum_gap

    page_h = enum_y + 160
    page_w = max(pkg_com_x + pkg_com_w + 40, prod_x + col_w + 40, enum_total_w + 120)

    # ── Associations UML ───────────────────────────────────────────────────────
    c.append(uml_assoc(cl, co, mult_src="1", mult_tgt="0..*", role_tgt="commandes", kind="one_to_many"))
    c.append(uml_assoc(co, cm, mult_src="1", mult_tgt="0..1", role_tgt="contrat", kind="one_to_one"))
    c.append(uml_assoc(cm, rc, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(cm, pd, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(cm, br, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(rc, smp, mult_src="1", mult_tgt="1..*", role_tgt="mouvements", kind="one_to_many"))
    c.append(uml_assoc(rc, ec, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(ec, rl, mult_src="1", mult_tgt="1", kind="one_to_one"))
    c.append(uml_assoc(pd, pf, mult_src="1", mult_tgt="1..*", role_tgt="produitsFinis", kind="one_to_many"))
    c.append(uml_assoc(pf, sf, mult_src="1", mult_tgt="1..*", role_tgt="entreesStock", kind="one_to_many"))
    c.append(uml_assoc(u, co, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, cm, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, rc, mult_src="1", mult_tgt="0..*", role_tgt="magasinier", kind="association"))
    c.append(uml_assoc(u, ec, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, rl, mult_src="1", mult_tgt="0..*", role_tgt="laborantin", kind="association"))
    c.append(uml_assoc(u, pd, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, br, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, al, mult_src="1", mult_tgt="0..*", role_tgt="destinataire", kind="association"))
    c.append(uml_assoc(cl, br, mult_src="1", mult_tgt="0..*", role_tgt="bonsRetrait", kind="one_to_many"))

    write_drawio(
        OUT_DIR / "diagramme_classes_MNL.drawio",
        "Classes MNL",
        c,
        page_width=page_w,
        page_height=page_h,
    )


# ── Diagramme de classes de conception (aligné Django / FK explicites) ───────

def _fk(field: str, target: str, optional: bool = False) -> str:
    opt = " {nullable}" if optional else ""
    return f"- {field} : Integer{{FK → {target}}}{opt}"


def gen_conception_classes() -> None:
    """Diagramme de conception : attributs + clés étrangères, conforme aux models Django."""
    reset_ids()
    c: list[str] = []
    c.append(title(
        "Diagramme de classes de conception — Système MNL (aligné application Django)",
        x=40, w=1700,
    ))

    W = 320
    BLUE = ("#DAE8FC", "#6C8EBF")
    GREEN = ("#D5E8D4", "#82B366")
    RED = ("#F8CECC", "#B85450")
    PURPLE = ("#E1D5E7", "#9673A6")
    YELLOW = ("#FFF2CC", "#D6B656")
    NO_OPS: list[str] = []

    utilisateur = (
        "Utilisateur",
        [
            "- id : Integer {PK}",
            "- nom : String",
            "- prenom : String",
            "- email : String {unique}",
            "- motDePasse : String {hashed}",
            "- telephone : String",
            "- role : Role <<enumeration>>",
            "- actif : Boolean",
            "- dateCreation : DateTime",
        ],
        NO_OPS, *BLUE,
    )
    client = (
        "Client",
        [
            "- id : Integer {PK}",
            "- nom : String",
            "- prenom : String",
            "- telephone : String",
            "- adresse : String",
            "- email : String",
            "- dateEnregistrement : Date",
            _fk("id_utilisateur", "Utilisateur", optional=True),
        ],
        NO_OPS, *BLUE,
    )
    commande = (
        "Commande",
        [
            "- id : Integer {PK}",
            "- numeroCommande : String {unique}",
            "- dateCommande : Date",
            "- quantiteKg : Float",
            "- statut : StatutCommande <<enumeration>>",
            "- observations : String",
            _fk("id_client", "Client"),
            _fk("id_comptable", "Utilisateur", optional=True),
        ],
        NO_OPS, *BLUE,
    )
    contrat = (
        "ContratMouture",
        [
            "- id : Integer {PK}",
            "- numeroContrat : String {unique}",
            "- dateContrat : Date",
            "- quantiteKg : Float",
            "- statut : StatutContrat <<enumeration>>",
            "- observations : String",
            _fk("id_client", "Client"),
            _fk("id_commande", "Commande", optional=True),
            _fk("id_comptable", "Utilisateur"),
        ],
        NO_OPS, *GREEN,
    )
    bon_retrait = (
        "BonRetrait",
        [
            "- id : Integer {PK}",
            "- numeroBon : String {unique}",
            "- dateRetrait : Date",
            "- quantiteSacs : Integer",
            "- factureReglee : Boolean",
            _fk("id_contrat", "ContratMouture"),
            _fk("id_client", "Client"),
            _fk("id_comptable", "Utilisateur"),
        ],
        NO_OPS, *YELLOW,
    )
    reception = (
        "Reception",
        [
            "- id : Integer {PK}",
            "- numeroBon : String {unique}",
            "- dateReception : Date",
            "- poidsBrutKg : Float",
            "- poidsNetKg : Float",
            "- observations : String",
            _fk("id_contrat", "ContratMouture"),
            _fk("id_magasinier", "Utilisateur"),
        ],
        NO_OPS, *GREEN,
    )
    stock_mp = (
        "StockMP",
        [
            "- id : Integer {PK}",
            "- quantiteDisponibleKg : Float",
            "- dateMaj : DateTime",
            _fk("id_reception", "Reception"),
        ],
        NO_OPS, *RED,
    )
    echantillon = (
        "Echantillon",
        [
            "- id : Integer {PK}",
            "- numeroEchantillon : String {unique}",
            "- dateEnvoiLabo : Date",
            "- statut : StatutEchantillon <<enumeration>>",
            _fk("id_reception", "Reception"),
            _fk("id_meunier", "Utilisateur"),
        ],
        NO_OPS, *PURPLE,
    )
    resultat = (
        "ResultatLaboratoire",
        [
            "- id : Integer {PK}",
            "- dateAnalyse : Date",
            "- tauxHumidite : Float",
            "- tauxAcidite : Float",
            "- tauxMatiereGrasse : Float",
            "- conforme : Boolean",
            "- observations : String",
            _fk("id_echantillon", "Echantillon"),
            _fk("id_laborantin", "Utilisateur"),
        ],
        NO_OPS, *PURPLE,
    )
    production = (
        "Production",
        [
            "- id : Integer {PK}",
            "- numeroProduction : String {unique}",
            "- dateDebut : Date",
            "- dateFin : Date {nullable}",
            "- quantiteTraiteeKg : Float",
            "- quantiteFarineKg : Float",
            "- pertesKg : Float",
            "- statut : StatutProduction <<enumeration>>",
            _fk("id_contrat", "ContratMouture"),
            _fk("id_meunier", "Utilisateur"),
        ],
        NO_OPS, *GREEN,
    )
    produit_fini = (
        "ProduitFini",
        [
            "- id : Integer {PK}",
            "- typeSac : TypeSac <<enumeration>>",
            "- nombreSacs : Integer",
            "- poidsTotalKg : Float",
            "- referenceLot : String",
            "- dateEnsachage : Date",
            _fk("id_production", "Production"),
        ],
        NO_OPS, *GREEN,
    )
    stock_farine = (
        "StockFarine",
        [
            "- id : Integer {PK}",
            "- typeFarine : String",
            "- quantiteSacs : Integer",
            "- quantiteKg : Float",
            "- dateMaj : DateTime",
            _fk("id_produit_fini", "ProduitFini"),
        ],
        NO_OPS, *RED,
    )
    alerte = (
        "Alerte",
        [
            "- id : Integer {PK}",
            "- type : TypeAlerte <<enumeration>>",
            "- message : String",
            "- lu : Boolean",
            "- dateCreation : DateTime",
            _fk("id_destinataire", "Utilisateur"),
        ],
        NO_OPS, *YELLOW,
    )

    Y0 = 55

    # Package accounts
    sec_x, sec_y = 40, Y0
    sec_w = W + 2 * PACKAGE_PAD
    sec_ix = sec_x + PACKAGE_PAD
    sec_iy = sec_y + PACKAGE_PAD + 18
    sec_items, sec_h = stack_classes([utilisateur, alerte], sec_ix, sec_iy, W)
    sec_pkg_h = sec_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» accounts / facturation", sec_x, sec_y, sec_w, sec_pkg_h))
    for _, cells in sec_items:
        c += cells
    u, al = sec_items[0][0], sec_items[1][0]

    # Package commercial (horizontal)
    com_x = sec_x + sec_w + PACKAGE_GAP
    com_y = Y0
    com_specs = [client, commande, contrat, bon_retrait]
    com_ix = com_x + PACKAGE_PAD
    com_iy = com_y + PACKAGE_PAD + 18
    com_gap = 45
    com_ids: list[str] = []
    com_cells: list[str] = []
    cx = com_ix
    max_com_h = 0
    for spec in com_specs:
        name, attrs, ops, fill, stroke = spec
        cid, cells = uml_class(name, attrs, ops, cx, com_iy, W, fill, stroke)
        com_ids.append(cid)
        com_cells += cells
        max_com_h = max(max_com_h, class_height(attrs, ops))
        cx += W + com_gap
    cl, co, cm, br = com_ids
    com_w = cx - com_ix + PACKAGE_PAD - com_gap
    com_h = max_com_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» clients / contrats / facturation", com_x, com_y, com_w, com_h))
    c += com_cells

    # Packages opérations
    ops_y = com_y + com_h + PACKAGE_GAP
    col_w = W + 2 * PACKAGE_PAD
    col_gap = PACKAGE_GAP
    ops_iy = ops_y + PACKAGE_PAD + 18

    mag_x = 40
    mag_ix = mag_x + PACKAGE_PAD
    mag_items, mag_h = stack_classes([reception, stock_mp], mag_ix, ops_iy, W)
    mag_pkg_h = mag_h + 2 * PACKAGE_PAD + 18
    c.append(uml_package("«app» magasin", mag_x, ops_y, col_w, mag_pkg_h))
    for _, cells in mag_items:
        c += cells
    rc, smp = mag_items[0][0], mag_items[1][0]

    lab_x = mag_x + col_w + col_gap
    lab_ix = lab_x + PACKAGE_PAD
    lab_items, lab_h = stack_classes([echantillon, resultat], lab_ix, ops_iy, W)
    lab_pkg_h = max(mag_pkg_h, lab_h + 2 * PACKAGE_PAD + 18)
    c.append(uml_package("«app» laboratoire", lab_x, ops_y, col_w, lab_pkg_h))
    for _, cells in lab_items:
        c += cells
    ec, rl = lab_items[0][0], lab_items[1][0]

    prod_x = lab_x + col_w + col_gap
    prod_ix = prod_x + PACKAGE_PAD
    prod_items, prod_h = stack_classes(
        [production, produit_fini, stock_farine], prod_ix, ops_iy, W,
    )
    prod_pkg_h = max(lab_pkg_h, prod_h + 2 * PACKAGE_PAD + 18)
    c.append(uml_package("«app» production", prod_x, ops_y, col_w, prod_pkg_h))
    for _, cells in prod_items:
        c += cells
    pd, pf, sf = prod_items[0][0], prod_items[1][0], prod_items[2][0]

    ops_row_h = max(mag_pkg_h, lab_pkg_h, prod_pkg_h)

    # Énumérations complètes
    enum_y = ops_y + ops_row_h + PACKAGE_GAP
    enum_gap = 30
    enums = [
        ("Role", "ADMIN, COMPTABLE, MAGASINIER, LABORANTIN, MEUNIER", 240),
        ("StatutCommande", "EN_ATTENTE, VALIDEE, REFUSEE, ANNULEE", 280),
        ("StatutContrat", "EN_ATTENTE, EN_COURS, TERMINE, ANNULE", 260),
        ("StatutEchantillon", "EN_ATTENTE, EN_COURS, TESTE", 240),
        ("StatutProduction", "EN_COURS, SUSPENDU, TERMINE", 240),
        ("TypeSac", "25KG, 50KG", 160),
        ("TypeAlerte", "RESULTAT_LABO, LIVRAISON_PRETE, RETARD, ANOMALIE", 300),
    ]
    enum_total_w = sum(ew for _, _, ew in enums) + enum_gap * (len(enums) - 1)
    c.append(uml_package("Types énumérés", 40, enum_y, enum_total_w + 2 * PACKAGE_PAD, 130))
    ex = 40 + PACKAGE_PAD
    ey = enum_y + PACKAGE_PAD + 20
    for ename, values, ew in enums:
        eid = nid()
        c.append(
            f'<mxCell id="{eid}" value="&lt;&lt;enumeration&gt;&gt;&#xa;{esc(ename)}" '
            f'style="swimlane;fontStyle=1;startSize=30;fillColor=#F5F5F5;'
            f'strokeColor=#666666;fontSize=11;html=1;" vertex="1" parent="1">'
            f'<mxGeometry x="{ex}" y="{ey}" width="{ew}" height="85" as="geometry"/></mxCell>'
        )
        c.append(
            f'<mxCell id="{nid()}" value="{esc(values)}" '
            f'style="text;strokeColor=none;fillColor=none;align=left;spacingLeft=8;fontSize=10;" '
            f'vertex="1" parent="{eid}">'
            f'<mxGeometry x="0" y="30" width="{ew}" height="50" as="geometry"/></mxCell>'
        )
        ex += ew + enum_gap

    page_h = enum_y + 160
    page_w = max(com_x + com_w + 40, prod_x + col_w + 40, enum_total_w + 120)

    # Associations (cardinalités conformes aux models Django)
    c.append(uml_assoc(cl, co, mult_src="1", mult_tgt="0..*", role_tgt="commandes", kind="one_to_many"))
    c.append(uml_assoc(cl, cm, mult_src="1", mult_tgt="0..*", role_tgt="contrats", kind="one_to_many"))
    c.append(uml_assoc(cl, br, mult_src="1", mult_tgt="0..*", role_tgt="bonsRetrait", kind="one_to_many"))
    c.append(uml_assoc(co, cm, mult_src="1", mult_tgt="0..1", role_tgt="contrat", kind="one_to_one"))
    c.append(uml_assoc(cm, rc, mult_src="1", mult_tgt="1", role_tgt="reception", kind="one_to_one"))
    c.append(uml_assoc(cm, pd, mult_src="1", mult_tgt="1", role_tgt="production", kind="one_to_one"))
    c.append(uml_assoc(cm, br, mult_src="1", mult_tgt="1", role_tgt="bonRetrait", kind="one_to_one"))
    c.append(uml_assoc(rc, smp, mult_src="1", mult_tgt="1..*", role_tgt="mouvements", kind="one_to_many"))
    c.append(uml_assoc(rc, ec, mult_src="1", mult_tgt="1", role_tgt="echantillon", kind="one_to_one"))
    c.append(uml_assoc(ec, rl, mult_src="1", mult_tgt="1", role_tgt="resultat", kind="one_to_one"))
    c.append(uml_assoc(pd, pf, mult_src="1", mult_tgt="1..*", role_tgt="produitsFinis", kind="one_to_many"))
    c.append(uml_assoc(pf, sf, mult_src="1", mult_tgt="1..*", role_tgt="entreesStock", kind="one_to_many"))
    c.append(uml_assoc(u, cl, mult_src="1", mult_tgt="0..*", role_tgt="enregistre_par", kind="association"))
    c.append(uml_assoc(u, co, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, cm, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, rc, mult_src="1", mult_tgt="0..*", role_tgt="magasinier", kind="association"))
    c.append(uml_assoc(u, ec, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, rl, mult_src="1", mult_tgt="0..*", role_tgt="laborantin", kind="association"))
    c.append(uml_assoc(u, pd, mult_src="1", mult_tgt="0..*", role_tgt="meunier", kind="association"))
    c.append(uml_assoc(u, br, mult_src="1", mult_tgt="0..*", role_tgt="comptable", kind="association"))
    c.append(uml_assoc(u, al, mult_src="1", mult_tgt="0..*", role_tgt="destinataire", kind="association"))

    write_drawio(
        OUT_DIR / "Diagramme de classe de conception.drawio",
        "Conception MNL",
        c,
        page_width=page_w,
        page_height=page_h,
    )


# ── MLD — Modèle Logique de Données (tables / PK / FK / types SQL) ───────────

MLD_ROW = 20
MLD_HEADER = 28


def mld_table(
    name: str,
    columns: list[str],
    x: int,
    y: int,
    w: int = 300,
    fill: str = "#DAE8FC",
    stroke: str = "#6C8EBF",
) -> tuple[str, list[str]]:
    """Table MLD Merise : en-tête + colonnes (# = PK, → = FK)."""
    tid = nid()
    cells: list[str] = []
    h = MLD_HEADER + len(columns) * MLD_ROW + 6
    cells.append(
        f'<mxCell id="{tid}" value="{esc(name)}" '
        f'style="swimlane;fontStyle=1;startSize={MLD_HEADER};fillColor={fill};'
        f'strokeColor={stroke};fontSize=12;align=center;html=1;whiteSpace=wrap;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    ay = MLD_HEADER
    for col in columns:
        style = "text;strokeColor=none;fillColor=none;align=left;spacingLeft=8;"
        if col.startswith("#"):
            style += "fontStyle=1;"
        elif "→" in col:
            style += "fontColor=#CC0000;"
        cells.append(
            f'<mxCell id="{nid()}" value="{esc(col)}" '
            f'style="{style}fontSize=10;html=1;whiteSpace=wrap;" '
            f'vertex="1" parent="{tid}">'
            f'<mxGeometry x="0" y="{ay}" width="{w}" height="{MLD_ROW}" as="geometry"/></mxCell>'
        )
        ay += MLD_ROW
    return tid, cells


def mld_height(n_cols: int) -> int:
    return MLD_HEADER + n_cols * MLD_ROW + 6


def mld_link(
    src: str,
    tgt: str,
    card_src: str = "1",
    card_tgt: str = "N",
    label: str = "",
) -> str:
    """Association MLD avec cardinalités Merise (1, N)."""
    lbl = label or f"({card_src},{card_tgt})"
    return uml_assoc(
        src, tgt,
        label=lbl,
        mult_src=card_src,
        mult_tgt=card_tgt,
        kind="one_to_many" if card_tgt.upper() in ("N", "0..N", "1..N") else "one_to_one",
    )


def gen_mld() -> None:
    """Génère le MLD aligné sur le schéma SQLite/Django du projet MNL."""
    reset_ids()
    c: list[str] = []
    c.append(title(
        "Modèle Logique de Données (MLD) — Système MNL — Minoterie de Lubumbashi",
        x=40, w=1900,
    ))

    W = 300
    GAP_X = 40
    GAP_Y = 50
    BLUE = ("#DAE8FC", "#6C8EBF")
    GREEN = ("#D5E8D4", "#82B366")
    RED = ("#F8CECC", "#B85450")
    PURPLE = ("#E1D5E7", "#9673A6")
    YELLOW = ("#FFF2CC", "#D6B656")

    # ── Définition des tables (noms de colonnes = Django/SQLite) ─────────────
    cols_u = [
        "# id : INTEGER",
        "nom : VARCHAR(100)",
        "prenom : VARCHAR(100)",
        "email : VARCHAR(254)  (UK)",
        "password : VARCHAR(128)",
        "telephone : VARCHAR(20)",
        "role : VARCHAR(20)",
        "is_active : BOOLEAN",
        "date_joined : DATETIME",
    ]
    cols_cl = [
        "# id : INTEGER",
        "nom : VARCHAR(100)",
        "prenom : VARCHAR(100)",
        "telephone : VARCHAR(20)",
        "adresse : TEXT",
        "email : VARCHAR(254)",
        "date_enregistrement : DATE",
        "enregistre_par_id : INTEGER  → UTILISATEUR  {null}",
    ]
    cols_co = [
        "# id : INTEGER",
        "numero_commande : VARCHAR(25)  (UK)",
        "date_commande : DATE",
        "quantite_kg : FLOAT",
        "statut : VARCHAR(20)",
        "observations : TEXT",
        "client_id : INTEGER  → CLIENT",
        "comptable_id : INTEGER  → UTILISATEUR  {null}",
        "date_creation : DATETIME",
    ]
    cols_cm = [
        "# id : INTEGER",
        "numero_contrat : VARCHAR(25)  (UK)",
        "date_contrat : DATE",
        "quantite_kg : FLOAT",
        "statut : VARCHAR(20)",
        "observations : TEXT",
        "client_id : INTEGER  → CLIENT",
        "commande_id : INTEGER  → COMMANDE  (UK,null)",
        "comptable_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_br = [
        "# id : INTEGER",
        "numero_bon : VARCHAR(25)  (UK)",
        "date_retrait : DATE",
        "quantite_sacs : INTEGER",
        "facture_reglee : BOOLEAN",
        "contrat_id : INTEGER  → CONTRAT_MOUTURE  (UK)",
        "client_id : INTEGER  → CLIENT",
        "comptable_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_rc = [
        "# id : INTEGER",
        "numero_bon : VARCHAR(25)  (UK)",
        "date_reception : DATE",
        "poids_brut_kg : FLOAT",
        "poids_net_kg : FLOAT",
        "observations : TEXT",
        "contrat_id : INTEGER  → CONTRAT_MOUTURE  (UK)",
        "magasinier_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_smp = [
        "# id : INTEGER",
        "quantite_disponible_kg : FLOAT",
        "date_maj : DATETIME",
        "reception_id : INTEGER  → RECEPTION",
    ]
    cols_ec = [
        "# id : INTEGER",
        "numero_echantillon : VARCHAR(25)  (UK)",
        "date_envoi_labo : DATE",
        "statut : VARCHAR(20)",
        "reception_id : INTEGER  → RECEPTION  (UK)",
        "meunier_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_rl = [
        "# id : INTEGER",
        "date_analyse : DATE",
        "taux_humidite : FLOAT",
        "taux_acidite : FLOAT",
        "taux_matiere_grasse : FLOAT",
        "conforme : BOOLEAN",
        "observations : TEXT",
        "echantillon_id : INTEGER  → ECHANTILLON  (UK)",
        "laborantin_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_pd = [
        "# id : INTEGER",
        "numero_production : VARCHAR(25)  (UK)",
        "date_debut : DATE",
        "date_fin : DATE  {null}",
        "quantite_traitee_kg : FLOAT",
        "quantite_farine_kg : FLOAT",
        "pertes_kg : FLOAT",
        "statut : VARCHAR(20)",
        "contrat_id : INTEGER  → CONTRAT_MOUTURE  (UK)",
        "meunier_id : INTEGER  → UTILISATEUR",
        "date_creation : DATETIME",
    ]
    cols_pf = [
        "# id : INTEGER",
        "type_sac : VARCHAR(5)",
        "nombre_sacs : INTEGER",
        "poids_total_kg : FLOAT",
        "reference_lot : VARCHAR(30)",
        "date_ensachage : DATE",
        "production_id : INTEGER  → PRODUCTION",
    ]
    cols_sf = [
        "# id : INTEGER",
        "type_farine : VARCHAR(50)",
        "quantite_sacs : INTEGER",
        "quantite_kg : FLOAT",
        "date_maj : DATETIME",
        "produit_fini_id : INTEGER  → PRODUIT_FINI",
    ]
    cols_al = [
        "# id : INTEGER",
        "type : VARCHAR(25)",
        "message : TEXT",
        "lu : BOOLEAN",
        "date_creation : DATETIME",
        "destinataire_id : INTEGER  → UTILISATEUR",
    ]

    Y1 = 55
    x = 40

    # Ligne 1 — flux commercial
    u, cx = mld_table("UTILISATEUR", cols_u, x, Y1, W, *BLUE)
    c += cx
    x += W + GAP_X

    cl, cx = mld_table("CLIENT", cols_cl, x, Y1, W, *BLUE)
    c += cx
    x += W + GAP_X

    co, cx = mld_table("COMMANDE", cols_co, x, Y1, W, *BLUE)
    c += cx
    x += W + GAP_X

    cm, cx = mld_table("CONTRAT_MOUTURE", cols_cm, x, Y1, W, *GREEN)
    c += cx
    x += W + GAP_X

    br, cx = mld_table("BON_RETRAIT", cols_br, x, Y1, W, *YELLOW)
    c += cx

    row1_h = max(mld_height(len(cols)) for cols in [
        cols_u, cols_cl, cols_co, cols_cm, cols_br,
    ])
    Y2 = Y1 + row1_h + GAP_Y
    x = 40

    # Ligne 2 — magasin + labo
    rc, cx = mld_table("RECEPTION", cols_rc, x, Y2, W, *GREEN)
    c += cx
    x += W + GAP_X

    smp, cx = mld_table("STOCK_MP", cols_smp, x, Y2, W, *RED)
    c += cx
    x += W + GAP_X

    ec, cx = mld_table("ECHANTILLON", cols_ec, x, Y2, W, *PURPLE)
    c += cx
    x += W + GAP_X

    rl, cx = mld_table("RESULTAT_LABORATOIRE", cols_rl, x, Y2, W, *PURPLE)
    c += cx
    x += W + GAP_X

    al, cx = mld_table("ALERTE", cols_al, x, Y2, W, *YELLOW)
    c += cx

    row2_h = max(mld_height(len(cols)) for cols in [
        cols_rc, cols_smp, cols_ec, cols_rl, cols_al,
    ])
    Y3 = Y2 + row2_h + GAP_Y
    x = 340

    # Ligne 3 — production
    pd, cx = mld_table("PRODUCTION", cols_pd, x, Y3, W, *GREEN)
    c += cx
    x += W + GAP_X

    pf, cx = mld_table("PRODUIT_FINI", cols_pf, x, Y3, W, *GREEN)
    c += cx
    x += W + GAP_X

    sf, cx = mld_table("STOCK_FARINE", cols_sf, x, Y3, W, *RED)
    c += cx

    row3_h = max(mld_height(len(cols)) for cols in [cols_pd, cols_pf, cols_sf])
    page_w = 40 + 5 * (W + GAP_X)
    page_h = Y3 + row3_h + 80

    # ── Associations MLD (cardinalités Merise) ────────────────────────────────
    c.append(mld_link(u, cl, "0", "N", "enregistre"))
    c.append(mld_link(cl, co, "1", "N", "passe"))
    c.append(mld_link(cl, cm, "1", "N", "contracte"))
    c.append(mld_link(cl, br, "1", "N", "retire"))
    c.append(mld_link(co, cm, "0", "1", "valide_en"))
    c.append(mld_link(cm, rc, "1", "1", "receptionne"))
    c.append(mld_link(cm, pd, "1", "1", "mouture"))
    c.append(mld_link(cm, br, "1", "1", "autorise"))
    c.append(mld_link(rc, smp, "1", "N", "mouvements"))
    c.append(mld_link(rc, ec, "1", "1", "preleve"))
    c.append(mld_link(ec, rl, "1", "1", "analyse"))
    c.append(mld_link(pd, pf, "1", "N", "ensachage"))
    c.append(mld_link(pf, sf, "1", "N", "entree_stock"))
    c.append(mld_link(u, co, "0", "N", "saisit"))
    c.append(mld_link(u, cm, "0", "N", "gere"))
    c.append(mld_link(u, rc, "0", "N", "receptionne"))
    c.append(mld_link(u, ec, "0", "N", "envoie"))
    c.append(mld_link(u, rl, "0", "N", "encode"))
    c.append(mld_link(u, pd, "0", "N", "produit"))
    c.append(mld_link(u, br, "0", "N", "delivre"))
    c.append(mld_link(u, al, "1", "N", "recoit"))

    # Légende
    leg_y = page_h - 10
    c.append(
        f'<mxCell id="{nid()}" value="{esc("Légende : # = clé primaire (PK)  |  → = clé étrangère (FK)  |  (UK) = unique  |  {null} = nullable")}" '
        f'style="text;html=1;align=left;fontSize=10;strokeColor=none;fillColor=#F5F5F5;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="40" y="{leg_y}" width="900" height="24" as="geometry"/></mxCell>'
    )
    page_h += 30

    write_drawio(
        OUT_DIR / "Diagramme MLD MNL.drawio",
        "MLD MNL",
        c,
        page_width=page_w,
        page_height=page_h,
    )


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
    gen_conception_classes()
    gen_mld()
    gen_use_cases()
    gen_sequence()
    gen_activity()
    print(f"\nTerminé — {OUT_DIR}/")


if __name__ == "__main__":
    main()
