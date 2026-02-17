
def generate_recommendations(score: int):
    if score >= 90:
        return ["El proyecto tiene buena salud estructural."]
    elif score >= 75:
        return ["Refactorizar funciones largas.", "Dividir archivos grandes."]
    else:
        return ["Revisar arquitectura general.", "Aplicar principios SOLID."]
