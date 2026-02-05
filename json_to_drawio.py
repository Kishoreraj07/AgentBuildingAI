# JSON to draw.io

import json
from xml.etree.ElementTree import Element, SubElement, ElementTree


def shape_style(node):
    """
    Map node type to draw.io shape style
    """
    if node["type"] == 5:      # Start / End
        shape = "shape=terminator"
    elif node["type"] == 3:    # Decision
        shape = "shape=rhombus"
    else:                      # Process
        shape = "rounded=1"

    return (
        f"{shape};"
        f"fillColor={node['fill']};"
        f"strokeColor={node['border']};"
        "whiteSpace=wrap;"
        "html=1;"
    )


def convert_json_to_drawio(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ---- mxfile root ----
    mxfile = Element(
        "mxfile",
        host="app.diagrams.net",
        agent="Python-JSON-Converter",
        version="22.1.0"
    )

    diagram = SubElement(mxfile, "diagram", name="Workflow")

    graph = SubElement(
        diagram,
        "mxGraphModel",
        dx="2000",
        dy="1000",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="2000",
        pageHeight="2000"
    )

    root = SubElement(graph, "root")

    # Mandatory root cells
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")

    # ---- Create nodes ----
    for node in data["nodes"]:
        cell = SubElement(
            root,
            "mxCell",
            id=str(node["id"] + 2),
            value=node["text"],
            style=shape_style(node),
            vertex="1",
            parent="1"
        )

        SubElement(
            cell,
            "mxGeometry",
            x=str(node["x"]),
            y=str(node["y"]),
            width=str(node["width"]),
            height=str(node["height"]),
            **{"as": "geometry"}
        )

    # ---- Create edges ----
    edge_id = 1000
    for arrow in data["arrows"]:
        edge = SubElement(
            root,
            "mxCell",
            id=str(edge_id),
            value=arrow.get("label", ""),
            style="edgeStyle=orthogonalEdgeStyle;endArrow=block;html=1;",
            edge="1",
            parent="1",
            source=str(arrow["start_id"] + 2),
            target=str(arrow["end_id"] + 2)
        )

        geom = SubElement(
            edge,
            "mxGeometry",
            relative="1",
            **{"as": "geometry"}
        )

        if "waypoints" in arrow:
            points = SubElement(geom, "Array", **{"as": "points"})
            for p in arrow["waypoints"]:
                SubElement(points, "mxPoint", x=str(p["x"]), y=str(p["y"]))

        edge_id += 1

    # ---- Write file ----
    ElementTree(mxfile).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"✅ draw.io file generated: {output_path}")


# if __name__ == "__main__":
#     convert_json_to_drawio(
#         json_path=r"C:\Users\Deepakkumar.b\Desktop\ABA_Dev\aba\workflow\workflow.json",
#         output_path=r"C:\Users\Deepakkumar.b\Desktop\ABA_Dev\aba\workflow\workflow.drawio"
#     )
