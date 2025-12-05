/*
 * PlayerGold SDK para Unreal Engine
 * Implementación del SDK para integración de blockchain PlayerGold
 */

#include "PlayerGoldSDK.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

void UPlayerGoldSDK::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    
    HttpModule = &FHttpModule::Get();
    TokenExpirationTime = 0.0;
    
    UE_LOG(LogTemp, Log, TEXT("PlayerGold SDK initialized"));
}

void UPlayerGoldSDK::Deinitialize()
{
    Super::Deinitialize();
    
    UE_LOG(LogTemp, Log, TEXT("PlayerGold SDK deinitialized"));
}

void UPlayerGoldSDK::InitializeSDK(const FString& InApiKey, const FString& InApiUrl)
{
    ApiKey = InApiKey;
    ApiUrl = InApiUrl;
    
    // Autenticar inmediatamente
    Authenticate();
}

void UPlayerGoldSDK::Authenticate()
{
    TSharedRef<IHttpRequest> Request = CreateRequest(TEXT("/auth/token"), TEXT("POST"));
    
    // Crear JSON body
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("api_key"), ApiKey);
    
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
    
    Request->SetContentAsString(OutputString);
    Request->OnProcessRequestComplete().BindUObject(this, &UPlayerGoldSDK::OnAuthenticationResponse);
    Request->ProcessRequest();
}

void UPlayerGoldSDK::OnAuthenticationResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid())
    {
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject))
        {
            AuthToken = JsonObject->GetStringField(TEXT("token"));
            int32 ExpiresIn = JsonObject->GetIntegerField(TEXT("expires_in"));
            TokenExpirationTime = FPlatformTime::Seconds() + ExpiresIn;
            
            UE_LOG(LogTemp, Log, TEXT("PlayerGold SDK authenticated successfully"));
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("PlayerGold SDK authentication failed"));
    }
}

void UPlayerGoldSDK::GetBalance(const FString& Address, FOnBalanceReceived OnSuccess, FOnError OnError)
{
    EnsureAuthenticated();
    
    FString Endpoint = FString::Printf(TEXT("/balance/%s"), *Address);
    TSharedRef<IHttpRequest> Request = CreateRequest(Endpoint, TEXT("GET"));
    
    Request->OnProcessRequestComplete().BindUObject(
        this,
        &UPlayerGoldSDK::OnBalanceResponse,
        OnSuccess,
        OnError
    );
    
    Request->ProcessRequest();
}

void UPlayerGoldSDK::OnBalanceResponse(
    FHttpRequestPtr Request,
    FHttpResponsePtr Response,
    bool bWasSuccessful,
    FOnBalanceReceived OnSuccess,
    FOnError OnError
)
{
    if (bWasSuccessful && Response.IsValid())
    {
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject))
        {
            float Balance = JsonObject->GetNumberField(TEXT("balance"));
            OnSuccess.ExecuteIfBound(Balance);
        }
        else
        {
            OnError.ExecuteIfBound(TEXT("Failed to parse balance response"));
        }
    }
    else
    {
        FString ErrorMsg = Response.IsValid() ? Response->GetContentAsString() : TEXT("Request failed");
        OnError.ExecuteIfBound(ErrorMsg);
    }
}

void UPlayerGoldSDK::CreateTransaction(
    const FString& FromAddress,
    const FString& ToAddress,
    float Amount,
    const FString& PrivateKey,
    FOnTransactionCreated OnSuccess,
    FOnError OnError
)
{
    EnsureAuthenticated();
    
    TSharedRef<IHttpRequest> Request = CreateRequest(TEXT("/transaction"), TEXT("POST"));
    
    // Crear JSON body
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("from_address"), FromAddress);
    JsonObject->SetStringField(TEXT("to_address"), ToAddress);
    JsonObject->SetNumberField(TEXT("amount"), Amount);
    JsonObject->SetStringField(TEXT("private_key"), PrivateKey);
    JsonObject->SetNumberField(TEXT("fee"), 0.01);
    
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);
    
    Request->SetContentAsString(OutputString);
    Request->OnProcessRequestComplete().BindUObject(
        this,
        &UPlayerGoldSDK::OnTransactionResponse,
        OnSuccess,
        OnError
    );
    
    Request->ProcessRequest();
}

void UPlayerGoldSDK::OnTransactionResponse(
    FHttpRequestPtr Request,
    FHttpResponsePtr Response,
    bool bWasSuccessful,
    FOnTransactionCreated OnSuccess,
    FOnError OnError
)
{
    if (bWasSuccessful && Response.IsValid())
    {
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
        
        if (FJsonSerializer::Deserialize(Reader, JsonObject))
        {
            FString TransactionHash = JsonObject->GetStringField(TEXT("transaction_hash"));
            OnSuccess.ExecuteIfBound(TransactionHash);
        }
        else
        {
            OnError.ExecuteIfBound(TEXT("Failed to parse transaction response"));
        }
    }
    else
    {
        FString ErrorMsg = Response.IsValid() ? Response->GetContentAsString() : TEXT("Request failed");
        OnError.ExecuteIfBound(ErrorMsg);
    }
}

void UPlayerGoldSDK::GetTransaction(const FString& TransactionHash)
{
    EnsureAuthenticated();
    
    FString Endpoint = FString::Printf(TEXT("/transaction/%s"), *TransactionHash);
    TSharedRef<IHttpRequest> Request = CreateRequest(Endpoint, TEXT("GET"));
    
    Request->ProcessRequest();
}

void UPlayerGoldSDK::GetNetworkStatus()
{
    TSharedRef<IHttpRequest> Request = CreateRequest(TEXT("/network/status"), TEXT("GET"));
    Request->ProcessRequest();
}

TSharedRef<IHttpRequest> UPlayerGoldSDK::CreateRequest(const FString& Endpoint, const FString& Verb)
{
    TSharedRef<IHttpRequest> Request = HttpModule->CreateRequest();
    
    Request->SetURL(ApiUrl + Endpoint);
    Request->SetVerb(Verb);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    
    // Agregar token de autenticación si está disponible
    if (!AuthToken.IsEmpty())
    {
        Request->SetHeader(TEXT("Authorization"), FString::Printf(TEXT("Bearer %s"), *AuthToken));
    }
    
    return Request;
}

void UPlayerGoldSDK::EnsureAuthenticated()
{
    // Re-autenticar si el token está por expirar (5 minutos antes)
    if (AuthToken.IsEmpty() || FPlatformTime::Seconds() >= (TokenExpirationTime - 300.0))
    {
        Authenticate();
    }
}
