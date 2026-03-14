# Financial Freedom API

A Litestar-based API for financial management.

## Setup

1. **Prerequisites**: Ensure you have [uv](https://docs.astral.sh/uv/) installed.
2. **Install Dependencies**:
   ```bash
   uv sync
   ```
3. **Environment Configuration**:
   The project uses a `.env` file to configure the Litestar application location. Ensure you have a `.env` file in the root directory with the following content:
   ```env
   LITESTAR_APP=main:app
   ```

## Running the Application

To start the development server with hot-reloading:

```bash
uv run litestar --app main:app run
```

The API will be available at `http://localhost:8000`.

### Troubleshooting

If port `8000` is already in use, you can specify a different port:

```bash
uv run litestar run --port 8001
```