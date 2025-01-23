import pygame


def draw_arrow(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 2,
        head_width: int = 4,
        head_height: int = 2,
):
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - head_height

    head_verts = [
        pygame.Vector2(0, head_height / 2),
        pygame.Vector2(head_width / 2, -head_height / 2),
        pygame.Vector2(-head_width / 2, -head_height / 2),
    ]

    translation = pygame.Vector2(
        0, arrow.length() - (head_height / 2)
    ).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    pygame.draw.polygon(surface, color, head_verts)

    if arrow.length() >= head_height:
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),
            pygame.Vector2(body_width / 2, body_length / 2),
            pygame.Vector2(body_width / 2, -body_length / 2),
            pygame.Vector2(-body_width / 2, -body_length / 2),
        ]
        translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)
