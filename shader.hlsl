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
    float2 wind;
};

Texture2D<int> source : register(t0);
Texture2D<float> humidity : register(t1);
Texture2D<float> noise : register(t2);

RWTexture2D<int> target : register(u0);
// RWTexture2D<float2> test : register(u0);

float remap(float value, float in_from, float in_to, float out_from, float out_to) {
    return out_from + (out_to - out_from) * (value - in_from) / (in_to - in_from);
}

int2 neighbors_check(uint2 origin, int type) {
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            if (i == 0 && j == 0) {
                continue;
            }

            int2 position = int2(origin) + int2(i, j);
            if (position.x >= 0 && position.x < size && position.y >= 0 && position.y < size) {
                if (source[position] == type) {
                    return position;
                }
            }
        }
    }

    return int2(-1, -1);
}

int next_state(uint2 position) {
    // Any -> Lightning
    if (noise[position] < lightning_prob) {
        return LIGHTNING;
    }

    uint state = source[position];

    // Lightning -> Fire
    if (state == LIGHTNING) {
        return FIRE;
    }

    // Fire -> Ash
    if (state == FIRE) {
        if (noise[position] < remap(humidity[position], 0.5, 1.5, .5, 1)) {
            return ASH;
        }
    }

    // Ash -> Empty
    if (state == ASH) {
        return EMPTY;
    }

    // Empty -> Plant
    if (state == EMPTY) {
        if (neighbors_check(position, PLANT).x != -1 && noise[position] < growth_prob) {
            return PLANT;
        }
    }

    // Plant -> Fire
    if (state == PLANT) {
        int2 fire_position = neighbors_check(position, FIRE);
        if (fire_position.x != -1 && fire_position.y != -1) {
            float2 fire_direction = normalize(float2(position) - float2(fire_position));
            float angle = acos(dot(fire_direction, wind));

            if (noise[position] < spread_prob * (2 - humidity[position]) * (angle / PI)) {
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

    // // Tests
    // uint2 fire_position = uint2(1, 1);
    // uint2 position = uint2(0, 0);
    // float2 fire_direction = normalize(float2(position.xy) - float2(fire_position.xy));
    // float angle = acos(dot(fire_direction.xy, wind.xy));

    // test[uint2(0, 0)] = fire_direction.xy;
    // test[uint2(1, 0)] = wind.xy;
    // test[uint2(2, 0)] = float2(angle, angle / PI);
}