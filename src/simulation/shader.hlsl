// Types
#define EMPTY 0
#define PLANT 1
#define FIRE 2
#define LIGHTNING 3
#define ASH 4
#define WATER 5

#define PI 3.14159265359

#define size 256

cbuffer Config : register(b0) {
    float growth_prob;
    float spread_prob;
    float lightning_prob;
    float humidity_change;
    float humidity_change_fire;
}

cbuffer Wind : register(b1) {
    float2 wind;
};

Texture2D<int> source : register(t0);
Texture2D<float> humidity : register(t1);
Texture2D<float> noise : register(t2);

RWTexture2D<int> target : register(u0);
RWTexture2D<float> out_humidity : register(u1);

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

void change_humidity(uint2 position, float change_value) {
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            int2 neighbor = int2(position) + int2(i, j);
            if (neighbor.x >= 0 && neighbor.x < size && neighbor.y >= 0 && neighbor.y < size) {
                out_humidity[neighbor] = change_value;
            }
        }
    }
}

int next_state(uint2 position) {
    uint state = source[position];

    // Leave Water Alone (Water -> Water)
    if (state == WATER) {
        return WATER;
    }

    // Any -> Lightning
    if (noise[position] < lightning_prob) {
        return LIGHTNING;
    }

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
            if (humidity_change != 0) {
                change_humidity(position, humidity_change);
            }

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
                if (humidity_change_fire != 0) {
                    change_humidity(position, humidity_change_fire);
                }

                return FIRE;
            }
        }
    }

    // Default
    return state;
}

[numthreads(16, 16, 1)] void main(uint3 tid : SV_DispatchThreadID) {
    target[tid.xy] = next_state(tid.xy);
}