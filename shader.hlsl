// Types
#define EMPTY 0
#define PLANT 1
#define FIRE 2
#define LIGHTNING 3
#define ASH 4

#define PI 3.14159265359

#define size 256

cbuffer Config : register(b0) {
    float growth_prob;
    float spread_prob;
    float lightning_prob;
}

cbuffer Wind : register(b1) {
    float windx;
    float windy;
};

Texture2D<int> source : register(t0);
Texture2D<float> humidity : register(t1);
Texture2D<float> noise : register(t2);

RWTexture2D<int> target : register(u0);

// float random(float2 p2) {
//     float3 p3 = float3(p2.xy, random_seed);
//     p3  = frac(p3 * .1031);
//     p3 += dot(p3, p3.zyx + 31.32);
//     return frac((p3.x + p3.y) * p3.z);
// }

int2 neighbors_check(uint2 position, int type) {
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            if (i == 0 && j == 0) {
                continue;
            }

            int2 neighbor = int2(position.xy) + int2(i, j);
            if (neighbor.x >= 0 && neighbor.x < size && neighbor.y >= 0 && neighbor.y < size) {
                if (source[neighbor.xy] == type) {
                    return neighbor;
                }
            }
        }
    }

    return int2(-1, -1);
}

int next_state(uint2 position) {
    // Any -> Lightning
    if (noise[position.xy] < lightning_prob) {
        return LIGHTNING;
    }

    uint state = source[position.xy];

    // Lightning -> Fire
    if (state == LIGHTNING) {
        return FIRE;
    }

    // Fire -> Ash
    if (state == FIRE) {
        if (noise[position.xy] < (2 - humidity[position.xy])) {
            return ASH;
        }
    }

    // Ash -> Empty
    if (state == ASH) {
        return EMPTY;
    }

    // Empty -> Plant
    if (state == EMPTY) {
        if (neighbors_check(position, PLANT).x != -1 && noise[position.xy] < growth_prob) {
            return PLANT;
        }
    }

    // Plant -> Fire
    if (state == PLANT) {
        int2 fire_position = neighbors_check(position, FIRE);
        if (fire_position.x != -1 && fire_position.y != -1) {
            int2 fire_direction = normalize(fire_position - position);
            float angle = acos(dot(fire_direction, normalize(float2(windx, windy))));

            if (noise[position.xy] < spread_prob * (2 - humidity[position.xy]) * (angle / PI)) {
                return FIRE;
            }
        }
    }

    // Default
    return state;
}

[numthreads(16, 16, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    target[tid.xy] = next_state(tid.xy);
}