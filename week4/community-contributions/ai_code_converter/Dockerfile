# Stage 1: Base development image
FROM ubuntu:22.04 AS builder

# Add metadata about build environment
LABEL org.opencontainers.image.title="CodeXchange AI Builder"
LABEL org.opencontainers.image.description="Multi-platform build environment for CodeXchange AI"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools and compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    build-essential \
    gcc \
    g++ \
    openjdk-17-jdk \
    curl \
    ca-certificates \
    git \
    nodejs \
    npm \
    perl \
    lua5.3 \
    php \
    r-base \
    ruby \
    rustc \
    cargo \
    mono-complete \
    mono-devel \
    mono-mcs \
    sqlite3 \
    unzip \
    && rm -rf /var/lib/apt/lists/*
    
# Install TypeScript
RUN npm install -g typescript

# Install Swift
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libc6-dev \
    libcurl4 \
    libedit2 \
    libgcc-9-dev \
    libpython3.10 \
    libsqlite3-0 \
    libstdc++-9-dev \
    libxml2 \
    libz3-dev \
    pkg-config \
    tzdata \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then \
        SWIFT_URL="https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz"; \
    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        SWIFT_URL="https://download.swift.org/swift-5.9.2-release/ubuntu2204-aarch64/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04-aarch64.tar.gz"; \
    else \
        echo "Unsupported architecture for Swift: $arch"; \
        exit 1; \
    fi && \
    curl -fL $SWIFT_URL | tar xz -C /opt && \
    ln -s /opt/swift-5.9.2-RELEASE-ubuntu22.04*/usr/bin/swift /usr/local/bin/swift

# Install Kotlin
RUN KOTLIN_VERSION=1.9.22 && \
    cd /tmp && \
    curl -LO "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" && \
    unzip "kotlin-compiler-${KOTLIN_VERSION}.zip" -d /opt && \
    rm "kotlin-compiler-${KOTLIN_VERSION}.zip" && \
    ln -s "/opt/kotlinc/bin/kotlin" /usr/local/bin/kotlin && \
    ln -s "/opt/kotlinc/bin/kotlinc" /usr/local/bin/kotlinc

# Install Julia based on architecture (with Windows WSL2 compatibility)
RUN arch=$(uname -m) && \
    echo "Detected architecture: $arch" && \
    if [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        echo "Installing ARM64 version of Julia" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/aarch64/1.9/julia-1.9.3-linux-aarch64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    elif [ "$arch" = "x86_64" ] || [ "$arch" = "amd64" ]; then \
        echo "Installing x86_64 version of Julia" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    else \
        echo "WARNING: Unknown architecture $arch, defaulting to x86_64" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    fi

# Install Go based on architecture (with Windows WSL2 compatibility)
RUN arch=$(uname -m) && \
    echo "Detected architecture for Go: $arch" && \
    if [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        echo "Installing ARM64 version of Go" && \
        curl -L https://go.dev/dl/go1.21.6.linux-arm64.tar.gz | tar -C /usr/local -xzf -; \
    elif [ "$arch" = "x86_64" ] || [ "$arch" = "amd64" ]; then \
        echo "Installing x86_64 version of Go" && \
        curl -L https://go.dev/dl/go1.21.6.linux-amd64.tar.gz | tar -C /usr/local -xzf -; \
    else \
        echo "WARNING: Unknown architecture $arch for Go, defaulting to x86_64" && \
        curl -L https://go.dev/dl/go1.21.6.linux-amd64.tar.gz | tar -C /usr/local -xzf -; \
    fi
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Create app user
RUN useradd -m -s /bin/bash app
WORKDIR /app

# Copy project files
COPY --chown=app:app . .

# Create and activate virtual environment
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM ubuntu:22.04

# Add metadata about runtime environment
LABEL org.opencontainers.image.title="AI CodeXchange"
LABEL org.opencontainers.image.description="Multi-platform AI CodeXchange application"
LABEL org.opencontainers.image.version="1.0"

# Create platform-specific label at build time
RUN echo "Building on $(uname -s) $(uname -m) architecture" > /platform-info.txt
LABEL org.opencontainers.image.platform="$(cat /platform-info.txt)"

# Install runtime dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    gcc \
    g++ \
    openjdk-17-jdk \
    curl \
    nodejs \
    npm \
    perl \
    lua5.3 \
    php \
    r-base \
    ruby \
    rustc \
    cargo \
    mono-complete \
    mono-devel \
    mono-mcs \
    sqlite3 \
    unzip \
    && rm -rf /var/lib/apt/lists/*
    
# Install TypeScript
RUN npm install -g typescript

# Install Swift
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libc6-dev \
    libcurl4 \
    libedit2 \
    libgcc-9-dev \
    libpython3.10 \
    libsqlite3-0 \
    libstdc++-9-dev \
    libxml2 \
    libz3-dev \
    pkg-config \
    tzdata \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ]; then \
        SWIFT_URL="https://download.swift.org/swift-5.9.2-release/ubuntu2204/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04.tar.gz"; \
    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        SWIFT_URL="https://download.swift.org/swift-5.9.2-release/ubuntu2204-aarch64/swift-5.9.2-RELEASE/swift-5.9.2-RELEASE-ubuntu22.04-aarch64.tar.gz"; \
    else \
        echo "Unsupported architecture for Swift: $arch"; \
        exit 1; \
    fi && \
    curl -fL $SWIFT_URL | tar xz -C /opt && \
    ln -s /opt/swift-5.9.2-RELEASE-ubuntu22.04*/usr/bin/swift /usr/local/bin/swift

# Install Kotlin
RUN KOTLIN_VERSION=1.9.22 && \
    cd /tmp && \
    curl -LO "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" && \
    unzip "kotlin-compiler-${KOTLIN_VERSION}.zip" -d /opt && \
    rm "kotlin-compiler-${KOTLIN_VERSION}.zip" && \
    ln -s "/opt/kotlinc/bin/kotlin" /usr/local/bin/kotlin && \
    ln -s "/opt/kotlinc/bin/kotlinc" /usr/local/bin/kotlinc

# Install Julia based on architecture (with Windows WSL2 compatibility)
RUN arch=$(uname -m) && \
    echo "Detected architecture: $arch" && \
    if [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then \
        echo "Installing ARM64 version of Julia" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/aarch64/1.9/julia-1.9.3-linux-aarch64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    elif [ "$arch" = "x86_64" ] || [ "$arch" = "amd64" ]; then \
        echo "Installing x86_64 version of Julia" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    else \
        echo "WARNING: Unknown architecture $arch, defaulting to x86_64" && \
        curl -fL https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz | tar xz -C /opt && \
        ln -s /opt/julia-1.9.3/bin/julia /usr/local/bin/julia; \
    fi

# Install Go runtime
COPY --from=builder /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Create app user
RUN useradd -m -s /bin/bash app
WORKDIR /app

# Copy virtual environment and application files from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# Create necessary directories with correct permissions
RUN mkdir -p /app/logs /app/downloads \
    && chown -R app:app /app/logs /app/downloads

# Verify installations with comprehensive platform information
RUN echo "======= PLATFORM & LANGUAGE VERIFICATION =======" && \
    echo "OS: $(uname -s)" && \
    echo "Architecture: $(uname -m)" && \
    echo "Kernel: $(uname -r)" && \
    echo "Host: $(uname -n)" && \
    echo "\n=== Language Installations ===" && \
    echo "Node.js: $(node --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "TypeScript: $(tsc --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Java: $(java -version 2>&1 | head -n 1 || echo 'NOT VERIFIED')" && \
    echo "Julia: $(julia --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Go: $(go version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Python: $(python3 --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Perl: $(perl -v 2>/dev/null | head -n 2 || echo 'NOT VERIFIED')" && \
    echo "Lua: $(lua5.3 -v 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "PHP: $(php --version 2>/dev/null | head -n 1 || echo 'NOT VERIFIED')" && \
    echo "R: $(R --version 2>/dev/null | head -n 1 || echo 'NOT VERIFIED')" && \
    echo "Ruby: $(ruby --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Rust: $(rustc --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "C#/Mono: $(mono-csc --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "SQLite: $(sqlite3 --version 2>/dev/null || echo 'NOT VERIFIED')" && \
    echo "Kotlin: $(kotlinc -version 2>&1 || echo 'NOT VERIFIED')" && \
    echo "C++: $(g++ --version 2>/dev/null | head -n 1 || echo 'NOT VERIFIED')" && \
    echo "\n=== Environment Variables ===" && \
    echo "PATH: $PATH" && \
    echo "======= VERIFICATION COMPLETE ======="

# Switch to non-root user
USER app

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/healthz || exit 1

# Set entrypoint and default command
ENTRYPOINT ["python3"]
CMD ["run.py"] 