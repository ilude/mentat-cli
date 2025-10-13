"""Tests for IoC container."""

import pytest

from mentat.ioc.container import Container


class TestContainer:
    """Test the IoC Container functionality."""

    @pytest.fixture
    def container(self):
        """Create a fresh container for each test."""
        return Container()

    def test_init_creates_empty_container(self, container):
        """Test that container initializes with empty registries."""
        assert len(container._singletons) == 0
        assert len(container._factories) == 0

    def test_register_singleton(self, container):
        """Test registering singleton instances."""
        test_instance = {"config": "test_value"}

        container.register_singleton("config", test_instance)

        assert "config" in container._singletons
        assert container._singletons["config"] is test_instance

    def test_register_factory(self, container):
        """Test registering factory functions."""

        def create_service():
            return {"service": "created"}

        container.register_factory("service", create_service)

        assert "service" in container._factories
        assert container._factories["service"] is create_service

    def test_resolve_singleton(self, container):
        """Test resolving singleton instances."""
        test_instance = {"config": "test_value"}
        container.register_singleton("config", test_instance)

        resolved = container.resolve("config")

        assert resolved is test_instance
        assert resolved == {"config": "test_value"}

    def test_resolve_factory(self, container):
        """Test resolving factory-created instances."""

        def create_service():
            return {"service": "created", "id": 123}

        container.register_factory("service", create_service)

        resolved = container.resolve("service")

        assert resolved == {"service": "created", "id": 123}
        # Should be cached as singleton after first resolve
        assert "service" in container._singletons
        assert container._singletons["service"] is resolved

    def test_resolve_factory_caches_result(self, container):
        """Test that factory results are cached as singletons."""
        call_count = 0

        def create_service():
            nonlocal call_count
            call_count += 1
            return {"service": "created", "call_count": call_count}

        container.register_factory("service", create_service)

        # First resolve should call factory
        first_result = container.resolve("service")
        assert first_result["call_count"] == 1

        # Second resolve should return cached result, not call factory again
        second_result = container.resolve("service")
        assert second_result is first_result
        assert second_result["call_count"] == 1
        assert call_count == 1

    def test_resolve_nonexistent_dependency_raises_keyerror(self, container):
        """Test that resolving non-existent dependency raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            container.resolve("nonexistent")

        assert "Dependency not found: nonexistent" in str(exc_info.value)

    def test_singleton_overrides_factory(self, container):
        """Test that singletons take precedence over factories."""

        def create_service():
            return {"from": "factory"}

        singleton_instance = {"from": "singleton"}

        # Register both factory and singleton for same key
        container.register_factory("service", create_service)
        container.register_singleton("service", singleton_instance)

        # Should resolve singleton, not factory
        resolved = container.resolve("service")
        assert resolved is singleton_instance
        assert resolved == {"from": "singleton"}

    def test_factory_can_override_previous_factory(self, container):
        """Test that later factory registrations override earlier ones."""

        def first_factory():
            return {"version": 1}

        def second_factory():
            return {"version": 2}

        container.register_factory("service", first_factory)
        container.register_factory("service", second_factory)

        resolved = container.resolve("service")
        assert resolved == {"version": 2}

    def test_singleton_can_override_previous_singleton(self, container):
        """Test that later singleton registrations override earlier ones."""
        first_instance = {"version": 1}
        second_instance = {"version": 2}

        container.register_singleton("config", first_instance)
        container.register_singleton("config", second_instance)

        resolved = container.resolve("config")
        assert resolved is second_instance
        assert resolved == {"version": 2}

    def test_factory_with_dependencies(self, container):
        """Test factory that depends on other registered services."""
        # Register a config singleton
        config = {"database_url": "sqlite://test.db"}
        container.register_singleton("config", config)

        # Register a factory that uses the config
        def create_database():
            cfg = container.resolve("config")
            return {"type": "database", "url": cfg["database_url"]}

        container.register_factory("database", create_database)

        # Resolve database service
        db = container.resolve("database")
        assert db == {"type": "database", "url": "sqlite://test.db"}

    def test_factory_exception_propagates(self, container):
        """Test that exceptions in factory functions propagate."""

        def failing_factory():
            raise ValueError("Factory failed")

        container.register_factory("failing_service", failing_factory)

        with pytest.raises(ValueError) as exc_info:
            container.resolve("failing_service")

        assert "Factory failed" in str(exc_info.value)

    def test_complex_dependency_graph(self, container):
        """Test resolving complex dependency relationships."""
        # Config
        container.register_singleton(
            "config", {"db_url": "sqlite://test.db", "api_key": "test_key"}
        )

        # Database service depends on config
        def create_db():
            config = container.resolve("config")
            return {"type": "db", "url": config["db_url"]}

        container.register_factory("db", create_db)

        # API service depends on config and db
        def create_api():
            config = container.resolve("config")
            db = container.resolve("db")
            return {"type": "api", "key": config["api_key"], "database": db}

        container.register_factory("api", create_api)

        # Resolve API service (should pull in all dependencies)
        api = container.resolve("api")

        assert api["type"] == "api"
        assert api["key"] == "test_key"
        assert api["database"]["type"] == "db"
        assert api["database"]["url"] == "sqlite://test.db"

    def test_multiple_containers_are_independent(self):
        """Test that multiple container instances are independent."""
        container1 = Container()
        container2 = Container()

        container1.register_singleton("service", {"container": 1})
        container2.register_singleton("service", {"container": 2})

        assert container1.resolve("service") == {"container": 1}
        assert container2.resolve("service") == {"container": 2}

    def test_empty_string_key_works(self, container):
        """Test that empty string can be used as a key."""
        test_instance = {"empty_key": True}
        container.register_singleton("", test_instance)

        resolved = container.resolve("")
        assert resolved is test_instance

    def test_none_value_can_be_registered(self, container):
        """Test that None can be registered as a singleton value."""
        container.register_singleton("none_service", None)

        resolved = container.resolve("none_service")
        assert resolved is None
