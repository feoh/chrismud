# Architecture

## Purpose

This document captures the current technical architecture of Plurludanta and reviews the implementation as it exists in the repository today. It is intentionally more detailed than the project `README` and is meant for contributors rather than end users.

## System Summary

Plurludanta is a single-process Python application with two primary entry points:

- `plurludanta.py` hosts a FastAPI application, manages persistence through SQLModel, seeds an initial world, and exposes both REST and WebSocket interfaces.
- `client.py` is an asynchronous command-line client that authenticates with the server, issues gameplay requests over HTTP, and listens for room-level events over WebSocket.

At runtime, the server uses SQLite as its backing store and SQLModel entities as both persistence models and API response objects.

## High-Level Architecture

### Server

The server is organized around a single module, [plurludanta.py](../plurludanta.py), which currently owns:

- database initialization
- FastAPI application construction
- authentication helpers
- HTTP route handlers
- gameplay logic
- WebSocket connection management
- initial world seeding

This is a compact layout that keeps the project easy to read at small scale, but it also means transport, domain, and persistence responsibilities are tightly coupled in one file.

### Client

The client in [client.py](../client.py) is a thin terminal interface. It:

- registers and logs in users with HTTP requests
- stores a bearer token in memory
- translates typed commands into REST calls
- opens a WebSocket connection for asynchronous room events
- prints state returned by the `look`, inventory, and messaging endpoints

### Persistence

The application uses SQLModel with a SQLite database file named `plurludanta.db`. Database setup happens at import time through `initialize_database()`, and table creation uses `SQLModel.metadata.create_all(engine)`.

Testing swaps the production session dependency with an in-memory SQLite engine backed by `StaticPool`, allowing isolated request-level tests without changing application code.

## Runtime Components

### HTTP API

The REST API handles:

- authentication: registration, login, logout, current player lookup
- gameplay: look, move, inventory, pickup, drop, say
- world CRUD: players, things, locations, exits, player-location links
- diagnostics: route listing

Gameplay endpoints rely on FastAPI dependency injection to resolve the current player from a bearer token.

### WebSocket Notifications

The `ConnectionManager` keeps an in-memory mapping of `player_id -> WebSocket`. It supports:

- accepting authenticated socket connections
- disconnecting sockets on close
- sending direct events to a player
- broadcasting location-scoped events by querying `PlayerLocation`

The WebSocket layer is used for lightweight ambient updates such as arrivals, departures, speech, pickups, and drops. It does not currently own authoritative game state; REST remains the source of truth.

### World Initialization

`initialize_world()` seeds two locations, two exits, and one item:

- `Limbo`
- `Garden`
- exit `garden` from Limbo to Garden
- exit `void` from Garden to Limbo
- item `flower` in Garden

Seeding is idempotent at a coarse level: if any `Location` already exists, the function returns without further work.

## Data Model

The SQLModel entities live under [models/](../models).

### `Player`

Defined in [models/player.py](../models/player.py).

- UUID primary key
- unique `name`
- optional `password_hash`

This model supports both the authenticated flow and the older unauthenticated `player/create` flow.

### `Location`

Defined in [models/location.py](../models/location.py).

- UUID primary key
- unique `name`
- free-form `description`

### `LocationExit`

Defined in [models/locationexit.py](../models/locationexit.py).

- UUID primary key
- exit `name`
- source `location`
- `destination`
- `description`

This models directed navigation edges between locations.

### `Thing`

Defined in [models/thing.py](../models/thing.py).

- UUID primary key
- `name`
- `description`
- nullable `location`
- nullable `owner`

A `Thing` is effectively in exactly one of two states:

- present in a location
- carried by a player

The model does not enforce that invariant at the database level.

### `PlayerLocation`

Defined in [models/playerlocation.py](../models/playerlocation.py).

- UUID primary key
- unique `player`
- `location`
- `description`

This acts as a join table describing where each player currently is. The unique constraint on `player` ensures one current location per player.

### `PlayerSession`

Defined in [models/session.py](../models/session.py).

- UUID primary key
- `player`
- unique indexed `token`
- `created_at`
- `last_seen`

Sessions are bearer-token based and are refreshed opportunistically when a token is resolved.

## Main Request Flows

### Registration and Login

1. `POST /auth/register` creates a `Player` with a SHA-256 password hash.
2. Registration also assigns the player to `Limbo` by creating a `PlayerLocation`.
3. `POST /auth/login` validates the hash and stores a new `PlayerSession`.
4. Subsequent authenticated requests use `Authorization: Bearer <token>`.

### Looking Around

1. `GET /player/look` resolves the current player through the auth dependency.
2. The server loads the player’s `PlayerLocation`.
3. It fetches the current `Location`, other players in that room, visible `Thing` rows, and available `LocationExit` rows.
4. The response is returned as a composed JSON document tailored to the client.

### Movement

1. `POST /player/move/{exit_name}` looks up the caller’s current room.
2. It finds an exit by `(location, name)`.
3. It updates the caller’s `PlayerLocation`.
4. It broadcasts leave and arrival events to sockets in the old and new rooms.

### Inventory Transfer

For pickup and drop:

1. Resolve the player and current location.
2. Select a `Thing` by name and current ownership/location state.
3. Mutate `owner` and `location`.
4. Commit the transaction.
5. Broadcast a room event over WebSocket.

## Testing Strategy

Tests live in [test_plurludanta.py](../test_plurludanta.py).

The suite currently covers:

- player CRUD
- authentication flows
- thing/location/exit CRUD
- core gameplay actions
- route listing

The tests use FastAPI `dependency_overrides` to replace the production session provider with an in-memory SQLite-backed session. This is a practical and effective pattern for endpoint-level verification.

The current suite is strongest at happy-path HTTP behavior. It does not meaningfully exercise:

- WebSocket behavior
- concurrent gameplay conflicts
- database integrity edge cases
- schema migration behavior
- startup/import side effects

## Technical Design Review

### What Works Well

#### 1. Small-system readability

For a compact project, the code is easy to follow. The request flows are direct, the tests are readable, and the models are small enough to understand quickly.

#### 2. Pragmatic dependency injection

Using FastAPI dependency injection for the session and current-player lookup keeps authentication and persistence wiring relatively clean for a single-module service.

#### 3. Clear room-centric game loop

The domain is modeled around rooms, exits, players, and things. That matches the client experience well and keeps the API semantics intuitive.

#### 4. Practical test isolation

The in-memory SQLite strategy used in tests is appropriate for the current scale and gives fast feedback on endpoint behavior.

### Main Design Risks

#### 1. Too much responsibility in `plurludanta.py`

The server module currently mixes:

- app bootstrapping
- database lifecycle
- authentication
- domain rules
- transport serialization
- WebSocket fan-out
- development seeding

This is the primary maintainability constraint in the repository. Feature growth will make change risk and merge friction increase quickly because most concerns converge on one file.

#### 2. Import-time side effects

The global `engine = initialize_database()` runs during import. That couples module import with file-backed database creation and table creation. It works for local development, but it makes startup behavior less explicit and complicates reuse in scripts, alternate deployments, and some test shapes.

#### 3. Weak separation between persistence schema and API schema

SQLModel entities are used directly across storage and API boundaries. That is convenient, but it makes it harder to evolve database shape independently of API contracts and encourages route handlers to return raw persistence objects.

#### 4. Authentication is functionally adequate but not production-grade

Passwords are hashed with unsalted SHA-256. That is simple, but it is not sufficient for real credential storage. Session invalidation is also coarse: logout deletes all sessions for the player rather than just the presented token.

#### 5. Domain invariants are enforced in code, not in schema

Examples:

- a `Thing` can theoretically have both `location` and `owner` set, or neither set
- exit names are not constrained to be unique within a location
- deleting players or locations does not show an explicit cascade strategy in the application layer

At the current size, the route handlers maintain enough discipline for normal flows, but data integrity will become fragile as more features or writers are introduced.

#### 6. In-memory WebSocket connection tracking limits deployment options

`ConnectionManager` keeps active sockets in process memory. That is acceptable for a single-process dev server, but it means:

- horizontal scaling is not supported
- reconnect semantics are best-effort only
- background workers cannot emit events
- socket state disappears on restart

#### 7. Transaction boundaries are narrow and optimistic

Operations like pickup, drop, and movement perform read-then-write flows without explicit locking or conflict handling. SQLite and the single-process posture reduce the immediate risk, but multi-client race conditions remain possible.

### Detailed Review By Area

#### API Design

The API is serviceable for development, but it mixes user-facing gameplay routes with low-level CRUD routes in the same public surface. That increases accidental misuse and makes authorization strategy inconsistent. For example, authenticated gameplay endpoints are protected, while several world-mutating CRUD endpoints are open.

Recommendation:

- split player gameplay APIs from administrative/world-building APIs
- apply an explicit authorization model to all mutating routes
- consider versioning once the external API is meant to be stable

#### Data Modeling

The domain model is minimal and understandable, but there are gaps around invariants and relationships. There are foreign keys, but not many relational helpers, constraints, or deletion policies. The current model works as a thin record layer rather than a strongly defended domain schema.

Recommendation:

- add constraints for item state and exit uniqueness
- define relationship fields if richer traversal is needed
- decide and document deletion/cascade behavior

#### Application Structure

The project would benefit most from modularization. The current implementation has already crossed the threshold where splitting by responsibility would improve clarity without adding unnecessary ceremony.

A practical next structure would be:

- `app.py` or `main.py` for FastAPI assembly
- `db.py` for engine/session lifecycle
- `auth.py` for password and token helpers
- `routes/` for transport handlers
- `services/` for game rules such as movement and inventory transfer
- `realtime.py` for connection management

That split would reduce coupling while preserving the project’s simplicity.

#### Security

The current design is acceptable for experimentation, not for untrusted deployment.

Specific concerns:

- password hashing should move to a dedicated password KDF such as Argon2 or bcrypt
- tokens are bearer credentials stored directly and appear to have no expiry or rotation policy
- open CRUD routes can mutate world state without authentication
- there is no rate limiting or brute-force protection

#### Operational Posture

The system assumes a local, single-node deployment. That is consistent with the code and the README usage, but it should be stated explicitly because the WebSocket model and SQLite persistence do not imply seamless production scaling.

Recommendation:

- document the intended deployment target clearly
- move startup tasks into explicit application lifecycle hooks
- add logging and configuration points before expanding runtime complexity

#### Test Coverage

The test suite is useful, but it primarily validates route success cases.

High-value missing tests include:

- WebSocket event delivery and disconnect handling
- duplicate-session and multi-session behavior
- unauthorized access to all mutating endpoints
- race-like scenarios around the same item or exit
- world initialization idempotency beyond the first existing location check

## Recommended Next Steps

### Near-Term

1. Split the server into modules by responsibility without changing behavior.
2. Replace SHA-256 password hashing with a proper password hashing library.
3. Move database setup and world seeding into explicit startup or CLI paths.
4. Tighten authorization on non-gameplay mutating routes.
5. Add tests for WebSocket behavior and edge-case failures.

### Mid-Term

1. Introduce service-layer functions for movement, item transfer, and chat.
2. Separate API response models from persistence entities.
3. Add stronger schema constraints around item state and exit uniqueness.
4. Define a session expiry and cleanup strategy.

### Longer-Term

1. Decide whether the project is a learning/reference codebase or a durable framework.
2. If durability matters, plan for migrations, structured configuration, logging, and multi-process event distribution.
3. If simplicity is the priority, document the single-node scope explicitly and keep the architecture intentionally small.

## Repository References

- [README.md](../README.md)
- [plurludanta.py](../plurludanta.py)
- [client.py](../client.py)
- [test_plurludanta.py](../test_plurludanta.py)
- [models/player.py](../models/player.py)
- [models/location.py](../models/location.py)
- [models/locationexit.py](../models/locationexit.py)
- [models/playerlocation.py](../models/playerlocation.py)
- [models/thing.py](../models/thing.py)
- [models/session.py](../models/session.py)
