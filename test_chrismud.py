import pytest
import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from chrismud import app, get_session
from sqlmodel.pool import StaticPool

@pytest.fixture(name="session")  
def session_fixture():  
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session  


@pytest.fixture(name="client")  
def client_fixture(session: Session):  
    def get_session_override():  
        return session
    app.dependency_overrides[get_session] = get_session_override  

    client = TestClient(app)  
    yield client  
    app.dependency_overrides.clear()  


class TestListRoutes:
    def test_list_routes(self, client: TestClient):
        response = client.get("/listroutes")
        assert response.status_code == 200
        routes = response.json()
        assert isinstance(routes, list)
        assert len(routes) > 0
        route_paths = [route["path"] for route in routes]
        assert "/listroutes" in route_paths


class TestPlayerRoutes:
    def test_list_players_empty(self, client: TestClient):
        response = client.get("/player/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_player(self, client: TestClient):
        response = client.post("/player/create/TestPlayer")
        assert response.status_code == 200
        player_id = response.json()
        assert isinstance(player_id, str)
        uuid.UUID(player_id)

    def test_list_players_with_data(self, client: TestClient):
        client.post("/player/create/Player1")
        client.post("/player/create/Player2")

        response = client.get("/player/list")
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 2
        assert players[0]["name"] == "Player1"
        assert players[1]["name"] == "Player2"

    def test_get_player(self, client: TestClient):
        create_response = client.post("/player/create/GetTestPlayer")
        player_id = create_response.json()

        response = client.get(f"/player/get/{player_id}")
        assert response.status_code == 200
        player = response.json()
        assert player["name"] == "GetTestPlayer"
        assert player["id"] == player_id

    def test_get_nonexistent_player(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/player/get/{fake_id}")
        assert response.status_code == 200
        assert response.json() is None

    def test_delete_player(self, client: TestClient):
        create_response = client.post("/player/create/DeleteTestPlayer")
        player_id = create_response.json()

response = client.delete(f"/player/delete/{player_id}")
        assert response.status_code == 200
        assert response.json() == player_id

        get_response = client.get(f"/player/get/{player_id}")
        assert get_response.json() is None

    def test_delete_nonexistent_player(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/player/delete/{fake_id}")
        assert response.status_code == 404


class TestThingRoutes:
    def test_list_things_empty(self, client: TestClient):
        response = client.get("/thing/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_thing(self, client: TestClient):
        response = client.post("/thing/create/TestThing")
        assert response.status_code == 200
        thing_id = response.json()
        assert isinstance(thing_id, str)
        uuid.UUID(thing_id)

    def test_list_things_with_data(self, client: TestClient):
        client.post("/thing/create/Thing1")
        client.post("/thing/create/Thing2")

        response = client.get("/thing/list")
        assert response.status_code == 200
        things = response.json()
        assert len(things) == 2
        assert things[0]["name"] == "Thing1"
        assert things[1]["name"] == "Thing2"

    def test_get_thing(self, client: TestClient):
        create_response = client.post("/thing/create/GetTestThing")
        thing_id = create_response.json()

        response = client.get(f"/thing/get/{thing_id}")
        assert response.status_code == 200
        thing = response.json()
        assert thing["name"] == "GetTestThing"
        assert thing["id"] == thing_id

    def test_get_nonexistent_thing(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/thing/get/{fake_id}")
        assert response.status_code == 200
        assert response.json() is None

    def test_delete_thing(self, client: TestClient):
        create_response = client.post("/thing/create/DeleteTestThing")
        thing_id = create_response.json()

        response = client.delete(f"/thing/delete/{thing_id}")
        assert response.status_code == 200
        assert response.json() == thing_id

        get_response = client.get(f"/thing/get/{thing_id}")
        assert get_response.json() is None

    def test_delete_nonexistent_thing(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/thing/delete/{fake_id}")
        assert response.status_code == 404


class TestLocationRoutes:
    def test_list_locations_empty(self, client: TestClient):
        response = client.get("/location/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_location(self, client: TestClient):
        response = client.post("/location/create/TestLocation/A test location description")
        assert response.status_code == 200
        location_id = response.json()
        assert isinstance(location_id, str)
        uuid.UUID(location_id)

    def test_list_locations_with_data(self, client: TestClient):
        client.post("/location/create/Location1/Description1")
        client.post("/location/create/Location2/Description2")

        response = client.get("/location/list")
        assert response.status_code == 200
        locations = response.json()
        assert len(locations) == 2
        assert locations[0]["name"] == "Location1"
        assert locations[0]["description"] == "Description1"
        assert locations[1]["name"] == "Location2"
        assert locations[1]["description"] == "Description2"

    def test_get_location(self, client: TestClient):
        create_response = client.post("/location/create/GetTestLocation/Get test description")
        location_id = create_response.json()

        response = client.get(f"/location/get/{location_id}")
        assert response.status_code == 200
        location = response.json()
        assert location["name"] == "GetTestLocation"
        assert location["description"] == "Get test description"
        assert location["id"] == location_id

    def test_get_nonexistent_location(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/location/get/{fake_id}")
        assert response.status_code == 200
        assert response.json() is None

    def test_delete_location(self, client: TestClient):
        create_response = client.post("/location/create/DeleteTestLocation/Delete test description")
        location_id = create_response.json()

        response = client.delete(f"/location/delete/{location_id}")
        assert response.status_code == 200
        assert response.json() == location_id

        get_response = client.get(f"/location/get/{location_id}")
        assert get_response.json() is None

    def test_delete_nonexistent_location(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/location/delete/{fake_id}")
        assert response.status_code == 404


class TestPlayerLocationRoutes:
    def test_create_playerlocation(self, client: TestClient):
        player_response = client.post("/player/create/TestPlayer")
        player_id = player_response.json()

        location_response = client.post("/location/create/TestLocation/Test description")
        location_id = location_response.json()

        response = client.post(f"/playerlocation/create/{player_id}/{location_id}")
        assert response.status_code == 200
        playerlocation_id = response.json()
        assert isinstance(playerlocation_id, str)
        uuid.UUID(playerlocation_id)

    def test_get_playerlocation(self, client: TestClient):
        player_response = client.post("/player/create/GetTestPlayer")
        player_id = player_response.json()

        location_response = client.post("/location/create/GetTestLocation/Get test description")
        location_id = location_response.json()

        create_response = client.post(f"/playerlocation/create/{player_id}/{location_id}")
        playerlocation_id = create_response.json()

        response = client.get(f"/playerlocation/get/{playerlocation_id}")
        assert response.status_code == 200
        playerlocation = response.json()
        assert playerlocation["player"] == player_id
        assert playerlocation["location"] == location_id
        assert playerlocation["id"] == playerlocation_id

    def test_get_nonexistent_playerlocation(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.get(f"/playerlocation/get/{fake_id}")
        assert response.status_code == 200
        assert response.json() is None

    def test_delete_playerlocation(self, client: TestClient):
        player_response = client.post("/player/create/DeleteTestPlayer")
        player_id = player_response.json()

        location_response = client.post("/location/create/DeleteTestLocation/Delete test description")
        location_id = location_response.json()

        create_response = client.post(f"/playerlocation/create/{player_id}/{location_id}")
        playerlocation_id = create_response.json()

        response = client.delete(f"/playerlocation/delete/{playerlocation_id}")
        assert response.status_code == 200
        assert response.json() == playerlocation_id

        get_response = client.get(f"/playerlocation/get/{playerlocation_id}")
        assert get_response.json() is None

    def test_delete_nonexistent_playerlocation(self, client: TestClient):
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/playerlocation/delete/{fake_id}")
        assert response.status_code == 404

    def test_create_playerlocation_with_nonexistent_player(self, client: TestClient):
        fake_player_id = str(uuid.uuid4())
        location_response = client.post("/location/create/TestLocation/Test description")
        location_id = location_response.json()

        response = client.post(f"/playerlocation/create/{fake_player_id}/{location_id}")
        assert response.status_code == 200
        playerlocation_id = response.json()
        uuid.UUID(playerlocation_id)

    def test_create_playerlocation_with_nonexistent_location(self, client: TestClient):
        player_response = client.post("/player/create/TestPlayer")
        player_id = player_response.json()
        fake_location_id = str(uuid.uuid4())

        response = client.post(f"/playerlocation/create/{player_id}/{fake_location_id}")
        assert response.status_code == 200
        playerlocation_id = response.json()
        uuid.UUID(playerlocation_id)



