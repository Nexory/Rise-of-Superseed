import pygame

def find_closest_target(unit, buckets, bucket_size, base):
    """
    Find the closest enemy unit or base within the unit's attack range from its current position.
    
    Args:
        unit: The unit object.
        buckets: Dictionary of spatial buckets containing units.
        bucket_size: Size of each spatial bucket.
        base: The enemy base (for player units) or player base (for enemy units).
    
    Returns:
        The closest target within attack range, or None if no target is found.
    """
    attack_range = unit.attack_range
    # Determine buckets to check based on attack range
    left_x = unit.x - attack_range
    right_x = unit.x + attack_range
    left_bucket = int(left_x // bucket_size)
    right_bucket = int(right_x // bucket_size)
    
    potential_targets = []
    
    # Check units in nearby buckets
    for b in range(left_bucket, right_bucket + 1):
        if b in buckets:
            for other in buckets[b]:
                if other.faction != unit.faction and other.state != "die":
                    distance = abs(unit.x - other.x)
                    if distance <= attack_range:
                        potential_targets.append((distance, other))
    
    # Check the base
    base_distance = abs(unit.x - base.x)
    if base_distance <= attack_range:
        potential_targets.append((base_distance, base))
    
    if potential_targets:
        potential_targets.sort(key=lambda x: x[0])
        return potential_targets[0][1]  # Return the closest target
    return None

def check_player_collisions(unit, buckets, bucket_size, enemy_base):
    """
    Collision logic for player units (direction == 1).
    
    Returns:
        tuple: (new_x, new_state, target)
        - new_x: Updated x position.
        - new_state: Updated state ("run", "idle", "hurt", or "attack").
        - target: Unit or base to attack, or None.
    """
    # Check if there's a target within attack range from current position
    target = find_closest_target(unit, buckets, bucket_size, enemy_base)
    if target:
        new_state = "attack"
        new_x = unit.x  # Stay in place if attacking
        return new_x, new_state, target
    
    # If no target in range, proceed with movement and collision checks
    new_x = unit.x + unit.speed * unit.direction
    unit_rect = pygame.Rect(new_x + 3, unit.y, 120, 192)  # Offset as in V2.29
    bucket_x = int(new_x // bucket_size)
    check_buckets = [bucket_x - 1, bucket_x, bucket_x + 1]
    
    blocking_unit = None  # Same faction, ahead
    enemy_unit = None     # Opposing faction
    target = None
    
    # Check unit collisions
    for b in check_buckets:
        if b not in buckets:
            continue
        for other in buckets[b]:
            if other is unit or other.state == "die":
                continue
            if unit_rect.colliderect(other.get_rect()):
                if other.faction == unit.faction and other.x > unit.x:  # Ahead for player
                    blocking_unit = other
                elif other.faction != unit.faction:
                    enemy_unit = other
                    break
        if enemy_unit:
            break
    
    # Handle enemy collision
    if enemy_unit:
        new_x = enemy_unit.x - 120  # Stop before enemy
        new_state = "idle" if unit.state != "hurt" else "hurt"
        if unit.in_attack_range(enemy_unit):
            new_state = "attack"
            target = enemy_unit
        return new_x, new_state, target
    
    # Handle same-faction blocking unit
    if blocking_unit:
        if blocking_unit.state in ["idle", "attack"]:
            new_x = blocking_unit.x - 120  # Stop behind
            new_state = "idle" if unit.state != "hurt" else "hurt"
        else:  # Blocking unit is moving
            new_state = "run" if unit.state != "hurt" else "hurt"
            target_x = blocking_unit.x - 120
            new_x = min(unit.x + unit.speed * unit.direction, target_x)
            if unit.speed > blocking_unit.speed:
                unit.speed = blocking_unit.speed
        return new_x, new_state, target
    
    # Check base collision
    if unit_rect.colliderect(enemy_base.get_rect()):
        new_x = unit.x  # Stay in place
        new_state = "idle" if unit.state != "hurt" else "hurt"
        if unit.in_attack_range(enemy_base):
            new_state = "attack"
            target = enemy_base
        return new_x, new_state, target
    
    # No collisions, move normally
    new_state = "run" if unit.state != "hurt" else "hurt"
    return new_x, new_state, None

def check_enemy_collisions(unit, buckets, bucket_size, player_base):
    """
    Collision logic for enemy units (direction == -1).
    
    Returns:
        tuple: (new_x, new_state, target)
        - new_x: Updated x position.
        - new_state: Updated state ("run", "idle", "hurt", or "attack").
        - target: Unit or base to attack, or None.
    """
    # Check if there's a target within attack range from current position
    target = find_closest_target(unit, buckets, bucket_size, player_base)
    if target:
        new_state = "attack"
        new_x = unit.x  # Stay in place if attacking
        return new_x, new_state, target
    
    # If no target in range, proceed with movement and collision checks
    new_x = unit.x + unit.speed * unit.direction  # direction = -1, moves left
    unit_rect = pygame.Rect(new_x + 3, unit.y, 120, 192)  # Consistent offset
    bucket_x = int(new_x // bucket_size)
    check_buckets = [bucket_x - 1, bucket_x, bucket_x + 1]
    
    blocking_unit = None  # Same faction, ahead (smaller x)
    enemy_unit = None     # Opposing faction (player units)
    target = None
    
    # Check unit collisions
    for b in check_buckets:
        if b not in buckets:
            continue
        for other in buckets[b]:
            if other is unit or other.state == "die":
                continue
            if unit_rect.colliderect(other.get_rect()):
                if other.faction == unit.faction and other.x < unit.x:  # Ahead for enemy
                    blocking_unit = other
                elif other.faction != unit.faction:
                    enemy_unit = other
                    break
        if enemy_unit:
            break
    
    # Handle enemy (player unit) collision
    if enemy_unit:
        new_x = enemy_unit.x + 120  # Stop before enemy (to the right)
        new_state = "idle" if unit.state != "hurt" else "hurt"
        if unit.in_attack_range(enemy_unit):
            new_state = "attack"
            target = enemy_unit
        return new_x, new_state, target
    
    # Handle same-faction blocking unit
    if blocking_unit:
        if blocking_unit.state in ["idle", "attack"]:
            new_x = unit.x  # Stay in place behind attacking/idle unit
            new_state = "idle" if unit.state != "hurt" else "hurt"
        else:  # Blocking unit is moving
            new_state = "run" if unit.state != "hurt" else "hurt"
            target_x = blocking_unit.x + 120
            new_x = max(unit.x + unit.speed * unit.direction, target_x)  # Don’t pass blocking unit
            if unit.speed > blocking_unit.speed:
                unit.speed = blocking_unit.speed
        return new_x, new_state, target
    
    # Check base collision
    if unit_rect.colliderect(player_base.get_rect()):
        new_x = unit.x  # Stay in place
        new_state = "idle" if unit.state != "hurt" else "hurt"
        if unit.in_attack_range(player_base):
            new_state = "attack"
            target = player_base
        return new_x, new_state, target
    
    # No collisions, move normally
    new_state = "run" if unit.state != "hurt" else "hurt"
    return new_x, new_state, None