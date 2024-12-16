from typing import List, Optional, Tuple, cast

import numpy as np
import pygame

from util import BLACK, RED, WHITE, Vector, Color
from camera import Camera
from input import InputManager
from node import Node


class CoordinateAxes:
    def __init__(
        self, color: Color, text_offset: Tuple[int, int] = (0, -15), font_size: int = 16
    ) -> None:
        self.color = color
        self.text_offset = np.array(text_offset)
        self.font = pygame.font.SysFont("Courier", font_size)

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        origin = np.array([0, 0, 0])
        for endpoint, label in zip([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ["x", "y", "z"]):
            endpoint3d = np.array(endpoint)

            draw_line3d(screen, camera, self.color, origin, endpoint3d)

            endpoint2d = camera.world_to_screen(cast(Vector, endpoint3d * 1.1))
            if endpoint2d is not None:
                text_position = tuple(
                    np.round(endpoint2d + self.text_offset).astype(int)
                )
                screen.blit(self.font.render(label, True, self.color), text_position)


def draw_line3d(
    screen: pygame.Surface,
    camera: Camera,
    color: Color,
    start: Vector,
    end: Vector,
    width: int = 1,
) -> None:
    start2d = camera.world_to_screen(start)
    end2d = camera.world_to_screen(end)
    if start2d is not None and end2d is not None:
        pygame.draw.line(screen, color, tuple(start2d), tuple(end2d), width)


def draw_circle3d(
    screen: pygame.Surface,
    camera: Camera,
    color: Color,
    center: Vector,
    normal: Vector,
    radius: float,
    n_points: int,
    width: int = 1,
) -> None:
    n1, n2, n3 = normal
    # Construct two vectors orthogonal to the normal and to each other, to use as basis for circle points
    if np.isclose(n1, 0):
        orth1 = np.array([1.0, 0.0, 0.0])
    elif np.isclose(n2, 0):
        orth1 = np.array([0.0, 1.0, 0.0])
    elif np.isclose(n3, 0):
        orth1 = np.array([0.0, 0.0, 1.0])
    else:
        orth1 = np.array([n2 * n3, -2 * n1 * n3, n1 * n2])
    orth1 /= np.linalg.norm(orth1)
    orth2 = np.cross(normal, orth1)

    angles = np.linspace(0, 2 * np.pi, n_points + 1)
    starts = center + radius * (
        np.cos(angles[:-1, np.newaxis]) * orth1
        + np.sin(angles[:-1, np.newaxis]) * orth2
    )
    ends = center + radius * (
        np.cos(angles[1:, np.newaxis]) * orth1 + np.sin(angles[1:, np.newaxis]) * orth2
    )
    for start, end in zip(starts, ends):
        draw_line3d(screen, camera, color, start, end, width)


class Circumcircle:
    def __init__(self, nodes: List[Node], color: Color) -> None:
        self.nodes = nodes
        self.color = color

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        for node in self.nodes:
            node.draw(screen, camera)

        params = self.get_circle_params()
        if params is not None:
            center, normal, radius = params
            center_node = Node(center, color=self.color)
            center_node.draw(screen, camera)
            draw_circle3d(
                screen, camera, self.color, center, normal, radius, n_points=20
            )

    def get_circle_params(self) -> Optional[Tuple[Vector, Vector, float]]:
        """Return `center, normal, radius` of circle through the three nodes, if the
        points aren't collinear. Return `None` if they are."""

        a = self.nodes[0].position
        b = self.nodes[1].position
        c = self.nodes[2].position
        a1, a2, a3 = a
        b1, b2, b3 = b
        c1, c2, c3 = c
        a_norm2 = np.sum(a**2)
        b_norm2 = np.sum(b**2)
        c_norm2 = np.sum(c**2)

        # Vector orthogonal to the plane spanned by vectors `b - a` and `c - a`
        normal = np.cross(b - a, c - a)

        A = np.array(
            [
                [b1 - a1, b2 - a2, b3 - a3],
                [c1 - b1, c2 - b2, c3 - b3],
                normal,
            ]
        )
        rhs = np.array(
            [0.5 * (b_norm2 - a_norm2), 0.5 * (c_norm2 - b_norm2), a.dot(normal)]
        )

        try:
            center = np.linalg.solve(A, rhs)
        except np.linalg.LinAlgError:
            return None

        radius = np.linalg.norm(center - a)

        return (
            cast(Vector, center),
            cast(Vector, normal / np.linalg.norm(normal)),
            cast(np.float64, radius),
        )


class App:
    def __init__(self, screen_size: Tuple[int, int]) -> None:
        self.camera = Camera(
            np.array([0.8, 0.8, -1.0]),
            yaw=-np.pi / 10,
            pitch=-np.pi / 8,
            focal_length=300,
            sensor_dimensions=screen_size,
        )
        self.nodes = [
            Node(np.array([0, 0, 0])),
            Node(np.array([0, 1, 1])),
            Node(np.array([1, 0, 0])),
        ]

        self.circle = Circumcircle(self.nodes, RED)
        self.coordinate_axes = CoordinateAxes(BLACK)

        self.input_manager = InputManager(self.nodes, self.camera)

    def update(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            self.input_manager.handle_event(event)

        return True

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(WHITE)
        self.coordinate_axes.draw(screen, self.camera)
        self.circle.draw(screen, self.camera)


def main():
    pygame.init()
    screen_size = (1200, 900)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Circumcircle 3d")
    app = App(screen_size)
    clock = pygame.time.Clock()

    while True:
        if not app.update():
            break
        clock.tick(60)
        app.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
