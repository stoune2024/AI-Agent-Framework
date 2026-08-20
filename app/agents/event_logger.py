import structlog

logger = structlog.get_logger()


class AgentEventLogger:
    async def handle(self, event: dict) -> None:
        event_name = event.get("event")

        if event_name == "on_chat_model_start":
            self._log_model_start(event)

        elif event_name == "on_chat_model_end":
            self._log_model_end(event)

        elif event_name == "on_tool_start":
            self._log_tool_start(event)

        elif event_name == "on_tool_end":
            self._log_tool_end(event)

        elif event_name == "on_chain_start":
            self._log_chain_start(event)

        elif event_name == "on_chain_end":
            self._log_chain_end(event)

        elif event_name == "on_chain_error":
            self._log_chain_error(event)

    def _log_model_start(self, event: dict) -> None:

        logger.info(
            "llm.started",
            run_id=event.get("run_id"),
            name=event.get("name"),
            tags=event.get("tags"),
        )

    def _log_model_end(self, event: dict) -> None:

        output = event.get("data", {}).get("output")

        usage = None

        if output is not None:
            usage_metadata = getattr(
                output,
                "usage_metadata",
                None,
            )

            if usage_metadata:
                usage = usage_metadata

        logger.info(
            "llm.completed",
            run_id=event.get("run_id"),
            name=event.get("name"),
            token_usage=usage,
        )

    def _log_tool_start(self, event: dict) -> None:

        data = event.get("data", {})

        logger.info(
            "tool.started",
            run_id=event.get("run_id"),
            tool=event.get("name"),
            arguments=data.get("input"),
        )

    def _log_tool_end(self, event: dict) -> None:

        data = event.get("data", {})

        logger.info(
            "tool.completed",
            run_id=event.get("run_id"),
            tool=event.get("name"),
            result=data.get("output"),
        )

    def _log_chain_start(self, event: dict) -> None:

        logger.info(
            "graph.node.started",
            run_id=event.get("run_id"),
            node=event.get("name"),
        )

    def _log_chain_end(self, event: dict) -> None:

        logger.info(
            "graph.node.completed",
            run_id=event.get("run_id"),
            node=event.get("name"),
        )

    def _log_chain_error(self, event: dict) -> None:

        logger.error(
            "graph.node.failed",
            run_id=event.get("run_id"),
            node=event.get("name"),
            error=event.get("data"),
        )
