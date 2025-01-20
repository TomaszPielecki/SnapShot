import os


def get_gallery_images(directory='static/screenshots'):
    """
    Pobiera listę obrazów z katalogu galerii.

    :param directory: Ścieżka do katalogu z obrazami
    :return: Lista ścieżek do obrazów
    """
    if not os.path.exists(directory):
        return []

    images = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            images.append(os.path.join(directory, filename))
    return images
